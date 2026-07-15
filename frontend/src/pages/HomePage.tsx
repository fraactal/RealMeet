import { useEffect } from "react";
import { Link } from "react-router-dom";

import { Button, Icon, SectionCard } from "../components/ui";

const steps = [
  { title: "Busca", description: "Explora profesionales publicados por categoria, especialidad o modalidad." },
  { title: "Revisa", description: "Abre el perfil, conoce su presentacion y consulta horarios disponibles." },
  { title: "Reserva", description: "Inicia sesion o crea tu cuenta para confirmar una hora desde el flujo real." },
];

const clientItems = ["Busqueda de profesionales", "Perfiles publicos", "Horarios disponibles", "Historial de reservas"];
const professionalItems = ["Perfil publico", "Disponibilidad semanal", "Gestion de reservas", "Metricas operativas"];

export function HomePage() {
  useEffect(() => {
    document.title = "RealMeet | Agenda profesional simple";
  }, []);

  return (
    <div className="space-y-14">
      <section className="grid min-h-[calc(100vh-9rem)] items-center gap-10 py-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="max-w-3xl">
          <span className="inline-flex rounded-full bg-brand-100 px-4 py-2 text-sm font-semibold text-brand-700">
            Agenda profesional para servicios de salud, legal y nuevas categorias
          </span>
          <h1 className="mt-5 text-4xl font-bold leading-tight text-ink-900 md:text-6xl">
            Encuentra profesionales y reserva una hora de forma simple.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-ink-600 md:text-lg">
            RealMeet ayuda a clientes y profesionales a coordinar reservas con perfiles claros, disponibilidad visible y paneles protegidos por rol.
          </p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <Link to="/professionals">
              <Button className="w-full sm:w-auto" size="lg">
                Buscar profesionales
              </Button>
            </Link>
            <Link to="/login">
              <Button className="w-full sm:w-auto" size="lg" variant="secondary">
                Acceso profesional
              </Button>
            </Link>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
          <div className="rounded-lg bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-4 border-b border-slate-200 pb-4">
              <div>
                <p className="text-sm font-semibold text-brand-700">Vista de reserva</p>
                <h2 className="mt-1 text-xl font-bold text-ink-900">Agenda clara para decidir</h2>
              </div>
              <span className="flex h-11 w-11 items-center justify-center rounded-md bg-brand-100 text-brand-700">
                <Icon name="calendar" />
              </span>
            </div>
            <div className="mt-4 space-y-3">
              {["Perfil profesional publicado", "Modalidad y especialidades visibles", "Horarios disponibles por fecha"].map((item) => (
                <div className="flex items-center gap-3 rounded-md border border-slate-200 bg-white p-3" key={item}>
                  <span className="flex h-8 w-8 items-center justify-center rounded-md bg-success-100 text-success-700">
                    <Icon className="h-4 w-4" name="check" />
                  </span>
                  <span className="text-sm font-semibold text-ink-700">{item}</span>
                </div>
              ))}
            </div>
            <div className="mt-5 grid grid-cols-3 gap-2">
              {["09:00 h", "10:00 h", "11:00 h"].map((time) => (
                <span className="rounded-md border border-brand-200 bg-white px-3 py-2 text-center text-sm font-semibold text-brand-700" key={time}>
                  {time}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <SectionCard title="Como funciona" description="Un flujo breve para pasar de busqueda a reserva.">
        <div className="grid gap-4 md:grid-cols-3">
          {steps.map((step, index) => (
            <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm" key={step.title}>
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-brand-100 text-sm font-bold text-brand-700">{index + 1}</span>
              <h2 className="mt-4 text-lg font-semibold text-ink-900">{step.title}</h2>
              <p className="mt-2 text-sm leading-6 text-ink-500">{step.description}</p>
            </article>
          ))}
        </div>
      </SectionCard>

      <div className="grid gap-5 lg:grid-cols-2">
        <SectionCard title="Para clientes" description="Herramientas reales para encontrar y administrar reservas.">
          <ul className="grid gap-3 sm:grid-cols-2">
            {clientItems.map((item) => (
              <li className="flex items-center gap-2 text-sm font-semibold text-ink-700" key={item}>
                <Icon className="h-4 w-4 text-brand-700" name="check" />
                {item}
              </li>
            ))}
          </ul>
        </SectionCard>
        <SectionCard title="Para profesionales" description="Base operativa para publicar disponibilidad y revisar agenda.">
          <ul className="grid gap-3 sm:grid-cols-2">
            {professionalItems.map((item) => (
              <li className="flex items-center gap-2 text-sm font-semibold text-ink-700" key={item}>
                <Icon className="h-4 w-4 text-brand-700" name="check" />
                {item}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <section className="rounded-lg border border-brand-200 bg-brand-50 p-6 md:p-8">
        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-ink-900">Comienza revisando profesionales disponibles</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-600">
              Explora el catalogo publico y, si encuentras un horario, inicia sesion o crea tu cuenta para continuar.
            </p>
          </div>
          <Link to="/professionals">
            <Button className="w-full md:w-auto">Explorar catalogo</Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
