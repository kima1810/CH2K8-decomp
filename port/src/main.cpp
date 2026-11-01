// ch2k8 - ReXGlue Recompiled Project
//
// Minimal app: boots the recompiled default.xex through the Xenos GPU plugin.
// Customize by overriding virtual hooks from rex::ReXApp (see the SvR 2008
// port's svr2008_app.h).

#include "generated/default/ch2k8_init.h"

#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/rex_app.h>

#include <chrono>
#include <memory>
#include <thread>

bool Ch2k8OpenFrameLog(const char *path);
void Ch2k8CloseFrameLog();
REXCVAR_DEFINE_STRING(
    ch2k8_frame_log, "", "CH2K8/Diagnostics",
    "Opt-in CSV of guest VdSwap intervals and call wall/CPU time");

#ifdef _WIN32
#include "../third_party/renderdoc_app.h"
#include <rex/ui/d3d12/d3d12_provider.h>
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
  void OnPostSetup() override {
    const auto frame_log = REXCVAR_GET(ch2k8_frame_log);
    if (!frame_log.empty() && !Ch2k8OpenFrameLog(frame_log.c_str()))
      REXLOG_WARN("CH2K8 frame log could not be opened: {}", frame_log);
    // GPU-plugin flags register dynamically; report their effective values
    // after setup so rendering comparisons can verify the requested profile.
    for (const auto *name :
         {"render_target_path_d3d12", "async_shader_compilation",
          "readback_resolve", "readback_memexport", "occlusion_query_enable",
          "host_present_from_non_ui_thread", "draw_resolution_scale_x",
          "draw_resolution_scale_y", "dxbc_switch",
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
      auto provider = graphics ? dynamic_cast<rex::ui::d3d12::D3D12Provider *>(
                                     graphics->provider())
                               : nullptr;
      if (!get_api ||
          !get_api(eRENDERDOC_API_Version_1_6_0,
                   reinterpret_cast<void **>(&capture)) ||
          !provider) {
        REXLOG_WARN("CH2K8 GPU capture unavailable: requires injected "
                    "RenderDoc and D3D12");
        return;
      }
      auto device = provider->GetDevice();
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
    Ch2k8CloseFrameLog();
    // Join before the runtime releases the device used by the capture thread.
    capture_thread_.request_stop();
    if (capture_thread_.joinable())
      capture_thread_.join();
  }

private:
  std::jthread capture_thread_;
};

REX_DEFINE_APP(ch2k8, Ch2k8App::Create)
