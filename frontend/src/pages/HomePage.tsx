import { Link } from "react-router-dom";

import { Card } from "../components/ui/Card";

export function HomePage() {
  return (
    <div className="space-y-10">
      <section className="grid gap-8 rounded-[2rem] bg-gradient-to-br from-ink via-brand to-slate-800 px-8 py-12 text-white lg:grid-cols-[1.3fr_1fr]">
        <div className="space-y-5">
          <span className="inline-flex rounded-full border border-white/20 px-4 py-2 text-sm">MVP SaaS para salud y servicios legales</span>
          <h1 className="text-4xl font-semibold tracking-tight lg:text-6xl">Agenda profesional, disponibilidad real y reservas sin fricción.</h1>
          <p className="max-w-2xl text-base text-slate-200 lg:text-lg">
            RealMeet conecta profesionales, clientes y administración en una plataforma sobria, preparada para crecer con reuniones online,
            automatizaciones y pagos futuros.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/professionals" className="rounded-full bg-white px-5 py-3 font-semibold text-ink">
              Ver profesionales
            </Link>
            <Link to="/login" className="rounded-full border border-white/30 px-5 py-3 font-semibold text-white">
              Acceder al panel
            </Link>
          </div>
        </div>
        <div className="grid gap-4">
          <Card title="Base del MVP">
            <ul className="space-y-2 text-sm text-slate-700">
              <li>Autenticacion con roles</li>
              <li>Perfil profesional y disponibilidad</li>
              <li>Reservas, metricas y backoffice minimo</li>
            </ul>
          </Card>
          <Card title="Preparado para escalar">
            <ul className="space-y-2 text-sm text-slate-700">
              <li>Meeting provider desacoplado</li>
              <li>Servicio de correos SMTP o modo log</li>
              <li>Docker Compose, migraciones y seed inicial</li>
            </ul>
          </Card>
        </div>
      </section>
    </div>
  );
}
