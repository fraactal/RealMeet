import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { normalizeApiError } from "../api/errors";
import { fetchMe, login } from "../api/queries";
import { Card } from "../components/ui/Card";
import { useAuthStore } from "../store/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const { setToken, setUser } = useAuthStore();
  const [email, setEmail] = useState("admin@realmeet.local");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = await login(email, password);
      setToken(token);
      const me = await fetchMe();
      setUser(me);
      navigate("/dashboard");
    } catch (error) {
      const apiError = normalizeApiError(error);
      if (import.meta.env.DEV) {
        console.error("[LoginPage]", apiError);
      }
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      <Card title="Acceso a RealMeet">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
            <input className="w-full rounded-xl border border-slate-300 px-4 py-3" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              className="w-full rounded-xl border border-slate-300 px-4 py-3"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <button disabled={loading} className="w-full rounded-xl bg-ink px-4 py-3 font-semibold text-white">
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
          <p className="text-xs text-slate-500">
            Demo: admin@realmeet.local / Admin123!, professional@realmeet.local / Professional123!, client@realmeet.local / Client123!
          </p>
        </form>
      </Card>
    </div>
  );
}
