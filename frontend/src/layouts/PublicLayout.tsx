import { Outlet } from "react-router-dom";

import { Navbar } from "../components/Navbar";

export function PublicLayout() {
  return (
    <div>
      <Navbar />
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
