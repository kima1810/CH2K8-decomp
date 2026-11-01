// ch2k8 - ReXGlue Recompiled Project
//
// Minimal app: boots the recompiled default.xex through the Xenos GPU plugin.
// Customize by overriding virtual hooks from rex::ReXApp (see the SvR 2008
// port's svr2008_app.h).

#include "generated/default/ch2k8_init.h"

#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/rex_app.h>
#include <rex/system.h>
#include <rex/system/gpu_plugin.h>
#include <rex/ui/presenter.h>

#include <chrono>
#include <cstdlib>
#include <memory>
#include <thread>

REXCVAR_DEFINE_STRING(ch2k8_renderer, "d3d12", "CH2K8/Graphics",
                      "Native graphics backend: d3d12 or vulkan")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

bool Ch2k8OpenFrameLog(const char *path);
void Ch2k8CloseFrameLog();
void Ch2k8ConfigureHotFunctions(int selected_mode, int selected_unpack,
                                int selected_store, const char *path);
void Ch2k8CloseHotLog();
REXCVAR_DEFINE_STRING(ch2k8_vector_pack, "optimized", "CH2K8/Performance",
                      "Packed-vector path: baseline, optimized, or compare")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_STRING(ch2k8_hot_log, "", "CH2K8/Diagnostics",
                      "Opt-in per-thread hot-function aggregate CSV");
REXCVAR_DEFINE_STRING(
    ch2k8_vector_unpack, "optimized", "CH2K8/Performance",
    "Unpack path within optimized packing: baseline, optimized, or compare")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_STRING(ch2k8_vector_store, "optimized", "CH2K8/Performance",
                      "Aligned byte-store path within optimized unpack: "
                      "baseline, optimized, or compare")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
bool Ch2k8SaveOutput(rex::ui::Presenter *presenter, const char *path);
REXCVAR_DEFINE_STRING(ch2k8_output_capture, "", "CH2K8/Diagnostics",
                      "Opt-in native guest-output BMP filename prefix");
REXCVAR_DEFINE_INT32(ch2k8_output_capture_delay, 60, "CH2K8/Diagnostics",
                     "Seconds before native output readback")
    .range(0, 3600);
REXCVAR_DEFINE_INT32(ch2k8_output_capture_count, 1, "CH2K8/Diagnostics",
                     "Number of native output readbacks")
    .range(1, 10);
REXCVAR_DEFINE_INT32(ch2k8_output_capture_interval, 60, "CH2K8/Diagnostics",
                     "Seconds between native output readbacks")
    .range(1, 3600);
REXCVAR_DEFINE_STRING(
    ch2k8_frame_log, "", "CH2K8/Diagnostics",
    "Opt-in CSV of guest VdSwap intervals and call wall/CPU time");

#ifdef _WIN32
#include "../third_party/renderdoc_app.h"
#include <rex/ui/d3d12/d3d12_provider.h>
#if REX_HAS_VULKAN
#include <rex/ui/vulkan/provider.h>
#endif
#include <windows.h>

REXCVAR_DEFINE_STRING(
    ch2k8_gpu_capture, "", "CH2K8/Diagnostics",
    "Opt-in RenderDoc capture filename prefix (requires injected RenderDoc)");
REXCVAR_DEFINE_INT32(
    ch2k8_gpu_capture_delay, 120, "CH2K8/Diagnostics",
    "Seconds after runtime setup before an automated GPU capture")
    .range(0, 3600);
#endif

class Ch2k8App : public rex::ReXApp {
public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp>
  Create(rex::ui::WindowedAppContext &ctx) {
    return std::unique_ptr<Ch2k8App>(
        new Ch2k8App(ctx, "ch2k8", PPCImageConfig));
  }

protected:
  void OnPreSetup(rex::RuntimeConfig &config) override {
    const auto renderer = REXCVAR_GET(ch2k8_renderer);
    if (renderer == "d3d12" || renderer == "vulkan") {
      config.graphics = rex::system::LoadGpuPlugin("xenos", renderer);
      if (config.graphics) {
        REXLOG_INFO("CH2K8 selected native renderer: {}", renderer);
        return;
      }
    }
    const auto message =
        "CH2K8 renderer '" + renderer +
        "' is unavailable. Vulkan requires the Vulkan-capable SDK build. "
        "See the runtime log.";
    REXLOG_ERROR("{}", message);
    rex::ShowSimpleMessageBox(rex::SimpleMessageBoxType::Error, message);
    // OnPreSetup has no failure return; prevent the SDK from falling back
    // to its default backend after an explicit renderer request fails.
    std::exit(EXIT_FAILURE);
  }

  void OnPostSetup() override {
    const auto pack = REXCVAR_GET(ch2k8_vector_pack);
    const auto unpack = REXCVAR_GET(ch2k8_vector_unpack);
    const auto store = REXCVAR_GET(ch2k8_vector_store);
    if (store != "baseline" && store != "optimized" && store != "compare") {
      REXLOG_ERROR("Invalid ch2k8_vector_store: {}", store);
      std::exit(EXIT_FAILURE);
    }
    if (pack != "baseline" && pack != "optimized" && pack != "compare") {
      REXLOG_ERROR("Invalid ch2k8_vector_pack: {}", pack);
      std::exit(EXIT_FAILURE);
    }
    if (unpack != "baseline" && unpack != "optimized" && unpack != "compare") {
      REXLOG_ERROR("Invalid ch2k8_vector_unpack: {}", unpack);
      std::exit(EXIT_FAILURE);
    }
    Ch2k8ConfigureHotFunctions(pack == "compare"     ? 2
                               : pack == "optimized" ? 1
                                                     : 0,
                               unpack == "compare"     ? 2
                               : unpack == "optimized" ? 1
                                                       : 0,
                               store == "compare"     ? 2
                               : store == "optimized" ? 1
                                                      : 0,
                               REXCVAR_GET(ch2k8_hot_log).c_str());
    REXLOG_INFO("CH2K8 packed-vector path: {}", pack);
    REXLOG_INFO("CH2K8 vector-unpack path: {}", unpack);
    REXLOG_INFO("CH2K8 vector-store path: {}", store);
    const auto output_prefix = REXCVAR_GET(ch2k8_output_capture);
    auto graphics = runtime()->graphics_system();
    if (!output_prefix.empty() && graphics && graphics->presenter()) {
      auto presenter = graphics->presenter();
      const int delay = REXCVAR_GET(ch2k8_output_capture_delay);
      const int count = REXCVAR_GET(ch2k8_output_capture_count);
      const int interval = REXCVAR_GET(ch2k8_output_capture_interval);
      output_thread_ = std::jthread([presenter, output_prefix, delay, count,
                                     interval](std::stop_token stop) {
        using namespace std::chrono_literals;
        for (int image = 0; image < count; ++image) {
          for (int tick = 0; tick < (image ? interval : delay) * 10; ++tick) {
            if (stop.stop_requested())
              return;
            std::this_thread::sleep_for(100ms);
          }
          if (stop.stop_requested())
            return;
          const auto path =
              output_prefix + "-" + std::to_string(image) + ".bmp";
          const bool success = Ch2k8SaveOutput(presenter, path.c_str());
          REXLOG_INFO("CH2K8 native output capture: {} success={}", path,
                      success);
        }
      });
    }
    const auto frame_log = REXCVAR_GET(ch2k8_frame_log);
    if (!frame_log.empty() && !Ch2k8OpenFrameLog(frame_log.c_str()))
      REXLOG_WARN("CH2K8 frame log could not be opened: {}", frame_log);
    // GPU-plugin flags register dynamically; report their effective values
    // after setup so rendering comparisons can verify the requested profile.
    for (const auto *name :
         {"render_target_path_d3d12", "render_target_path_vulkan",
          "async_shader_compilation", "readback_resolve", "readback_memexport",
          "occlusion_query_enable", "host_present_from_non_ui_thread",
          "draw_resolution_scale_x", "draw_resolution_scale_y", "dxbc_switch",
          "d3d12_pipeline_creation_threads",
          "execute_unclipped_draw_vs_on_cpu"}) {
      REXLOG_INFO("CH2K8 rendering configuration: {}={}", name,
                  rex::cvar::GetFlagByName(name));
    }
#ifdef _WIN32
    const auto prefix = REXCVAR_GET(ch2k8_gpu_capture);
    if (!prefix.empty()) {
      auto module = GetModuleHandleW(L"renderdoc.dll");
      auto get_api = module ? reinterpret_cast<pRENDERDOC_GetAPI>(
                                  GetProcAddress(module, "RENDERDOC_GetAPI"))
                            : nullptr;
      RENDERDOC_API_1_6_0 *capture = nullptr;
      auto graphics = runtime()->graphics_system();
      RENDERDOC_DevicePointer device = nullptr;
      if (graphics) {
        if (auto provider = dynamic_cast<rex::ui::d3d12::D3D12Provider *>(
                graphics->provider())) {
          device = provider->GetDevice();
        }
#if REX_HAS_VULKAN
        if (auto provider = dynamic_cast<rex::ui::vulkan::VulkanProvider *>(
                graphics->provider())) {
          device = RENDERDOC_DEVICEPOINTER_FROM_VKINSTANCE(
              provider->vulkan_instance()->instance());
        }
#endif
      }
      if (!get_api ||
          !get_api(eRENDERDOC_API_Version_1_6_0,
                   reinterpret_cast<void **>(&capture)) ||
          !device) {
        REXLOG_WARN("CH2K8 GPU capture unavailable: requires injected "
                    "RenderDoc and a supported native graphics provider");
        return;
      }
      const int delay = REXCVAR_GET(ch2k8_gpu_capture_delay);
      capture_thread_ =
          std::jthread([capture, device, prefix, delay](std::stop_token stop) {
            using namespace std::chrono_literals;
            for (int tick = 0; tick < delay * 10; ++tick) {
              if (stop.stop_requested())
                return;
              std::this_thread::sleep_for(100ms);
            }
            if (stop.stop_requested() || capture->IsFrameCapturing())
              return;
            capture->SetCaptureFilePathTemplate(prefix.c_str());
            REXLOG_INFO("CH2K8 GPU capture: starting timed device capture");
            capture->StartFrameCapture(device, nullptr);
            if (!capture->IsFrameCapturing()) {
              REXLOG_WARN("CH2K8 GPU capture: start failed");
              return;
            }
            // Capture off-screen guest submissions across host presentation
            // calls.
            for (int tick = 0; tick < 8 && !stop.stop_requested(); ++tick)
              std::this_thread::sleep_for(100ms);
            const auto success = capture->EndFrameCapture(device, nullptr);
            REXLOG_INFO("CH2K8 GPU capture: completed success={}", success);
          });
    }
#endif
  }

  void OnShutdown() override {
    Ch2k8CloseHotLog();
    Ch2k8CloseFrameLog();
    output_thread_.request_stop();
    if (output_thread_.joinable())
      output_thread_.join();
    // Join before the runtime releases the device used by the capture thread.
    capture_thread_.request_stop();
    if (capture_thread_.joinable())
      capture_thread_.join();
  }

private:
  std::jthread output_thread_;
  std::jthread capture_thread_;
};

REX_DEFINE_APP(ch2k8, Ch2k8App::Create)
