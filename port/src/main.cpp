// ch2k8 - ReXGlue Recompiled Project
//
// Minimal app: boots the recompiled default.xex through the Xenos GPU plugin.
// Customize by overriding virtual hooks from rex::ReXApp (see the SvR 2008 port's svr2008_app.h).

#include "generated/default/ch2k8_init.h"

#include <rex/rex_app.h>
#include <rex/cvar.h>
#include <rex/logging.h>

#include <memory>

class Ch2k8App : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<Ch2k8App>(new Ch2k8App(ctx, "ch2k8", PPCImageConfig));
  }

 protected:
  void OnPostSetup() override {
    // GPU-plugin flags register dynamically; report their effective values
    // after setup so rendering comparisons can verify the requested profile.
    for (const auto* name : {"render_target_path_d3d12", "async_shader_compilation",
                             "readback_resolve", "readback_memexport",
                             "occlusion_query_enable"}) {
      REXLOG_INFO("CH2K8 rendering configuration: {}={}", name,
                  rex::cvar::GetFlagByName(name));
    }
  }
};

REX_DEFINE_APP(ch2k8, Ch2k8App::Create)
