import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { normalizeApiError } from "../api/errors";
import { fetchMe, login } from "../api/queries";
import { Button, ErrorState, Input, Label, SectionCard } from "../components/ui";
import { useAuthStore } from "../store/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const { setToken, setUser } = useAuthStore();
  const [email, setEmail] = useState("admin@realmeet.local");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Iniciar sesion | RealMeet";
  }, []);

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
    <div className="mx-auto grid max-w-5xl gap-8 py-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="flex flex-col justify-center">
        <span className="inline-flex w-fit rounded-full bg-brand-100 px-4 py-2 text-sm font-semibold text-brand-700">Acceso protegido</span>
        <h1 className="mt-5 text-3xl font-bold text-ink-900 md:text-5xl">Ingresa a tu espacio RealMeet</h1>
        <p className="mt-4 text-sm leading-6 text-ink-600">
          Clientes, profesionales y administradores acceden al panel que corresponde segun su rol.
        </p>
      </div>

      <SectionCard title="Iniciar sesion" description="Usa tus credenciales para continuar.">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-1">
            <Label htmlFor="login-email">Email</Label>
            <Input id="login-email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="login-password">Password</Label>
            <Input
              id="login-password"
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          {error ? <ErrorState title="No pudimos iniciar sesion" message={error} /> : null}
          <Button className="w-full" isLoading={loading} type="submit">
            Ingresar
          </Button>
          <p className="text-center text-sm text-ink-500">
            ¿Aun no tienes cuenta?{" "}
            <Link className="font-semibold text-brand-700 hover:text-brand-600" to="/register">
              Crear cuenta cliente
            </Link>
          </p>
          <p className="rounded-md bg-slate-50 p-3 text-xs leading-5 text-ink-500">
            Demo local: admin@realmeet.local / Admin123!, professional@realmeet.local / Professional123!, client@realmeet.local / Client123!
          </p>
        </form>
      </SectionCard>
    </div>
  );
}
