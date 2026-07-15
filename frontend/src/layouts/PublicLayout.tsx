import { Outlet } from "react-router-dom";

import { PublicFooter } from "../components/public/PublicFooter";
import { PublicHeader } from "../components/public/PublicHeader";

export function PublicLayout() {
  return (
    <div className="min-h-screen">
      <PublicHeader />
      <main className="mx-auto max-w-7xl px-5 py-8 md:py-10">
        <Outlet />
      </main>
      <PublicFooter />
    </div>
  );
}
