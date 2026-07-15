import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { normalizeApiError } from "../api/errors";
import { registerClient } from "../api/queries";
import { Button, ErrorState, Input, Label, SectionCard } from "../components/ui";

export function RegisterPage() {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Crear cuenta | RealMeet";
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await registerClient({
        user: {
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          phone: phone.trim() || null,
          role: "client",
        },
        client_profile: null,
      });
      navigate("/login");
    } catch (error) {
      setError(normalizeApiError(error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl gap-8 py-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="flex flex-col justify-center">
        <span className="inline-flex w-fit rounded-full bg-brand-100 px-4 py-2 text-sm font-semibold text-brand-700">Cuenta cliente</span>
        <h1 className="mt-5 text-3xl font-bold text-ink-900 md:text-5xl">Crea una cuenta para reservar</h1>
        <p className="mt-4 text-sm leading-6 text-ink-600">
          El registro permite confirmar reservas y revisar tu historial desde el panel cliente.
        </p>
      </div>

      <SectionCard title="Datos de acceso" description="Completa los campos reales requeridos para crear una cuenta cliente.">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="register-first-name">Nombre</Label>
              <Input id="register-first-name" autoComplete="given-name" required value={firstName} onChange={(event) => setFirstName(event.target.value)} />
            </div>
            <div className="space-y-1">
              <Label htmlFor="register-last-name">Apellido</Label>
              <Input id="register-last-name" autoComplete="family-name" required value={lastName} onChange={(event) => setLastName(event.target.value)} />
            </div>
          </div>
          <div className="space-y-1">
            <Label htmlFor="register-email">Email</Label>
            <Input id="register-email" autoComplete="email" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="register-phone">Telefono</Label>
            <Input id="register-phone" autoComplete="tel" value={phone} onChange={(event) => setPhone(event.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="register-password">Password</Label>
            <Input
              id="register-password"
              autoComplete="new-password"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          {error ? <ErrorState title="No pudimos crear la cuenta" message={error} /> : null}
          <Button className="w-full" isLoading={loading} type="submit">
            Crear cuenta
          </Button>
          <p className="text-center text-sm text-ink-500">
            ¿Ya tienes cuenta?{" "}
            <Link className="font-semibold text-brand-700 hover:text-brand-600" to="/login">
              Iniciar sesion
            </Link>
          </p>
        </form>
      </SectionCard>
    </div>
  );
}
