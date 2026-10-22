// ch2k8 - ReXGlue Recompiled Project
//
// Minimal app: boots the recompiled default.xex through the Xenos GPU plugin.
// Customize by overriding virtual hooks from rex::ReXApp (see the SvR 2008 port's svr2008_app.h).

#include "generated/default/ch2k8_init.h"

#include <rex/rex_app.h>

#include <memory>

class Ch2k8App : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<Ch2k8App>(new Ch2k8App(ctx, "ch2k8", PPCImageConfig));
  }
};

REX_DEFINE_APP(ch2k8, Ch2k8App::Create)
