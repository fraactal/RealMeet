import { Avatar, Badge, Button, Card, EmptyState, ErrorState, Icon, Input, Label, LoadingState, PageHeader, SectionCard, Select, StatusBadge, Textarea } from "../components/ui";
import { formatDateTime, formatLongDate, formatTime } from "../utils/dates";
import { getAppointmentStatusLabel, getConsultationModeLabel, getMeetingStatusLabel } from "../utils/labels";

const sampleDate = "2026-07-15T10:00:00-04:00";

export function DesignSystemPage() {
  return (
    <main className="min-h-screen px-6 py-8">
      <div className="mx-auto max-w-7xl space-y-8 pb-12">
      <PageHeader
        title="RealMeet Design System"
        description="Referencia interna de desarrollo para revisar componentes base del submodulo 10.1. Esta ruta no esta enlazada en la navegacion productiva."
        actions={
          <>
            <Button variant="secondary">Accion secundaria</Button>
            <Button>Accion principal</Button>
          </>
        }
      />

      <SectionCard title="Paleta y fondos" description="Tokens principales para marca, superficies, texto y estados.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Marca", "bg-brand-700 text-white", "#0b5563"],
            ["Superficie", "bg-surface-card text-ink-900", "#ffffff"],
            ["Exito", "bg-success-100 text-success-700", "#17633a"],
            ["Pendiente", "bg-warning-100 text-warning-700", "#8a5a00"],
            ["Error", "bg-danger-100 text-danger-700", "#9f2a2a"],
            ["Informacion", "bg-info-100 text-info-700", "#1e5b8f"],
            ["Texto", "bg-ink-900 text-white", "#102a43"],
            ["Fondo", "bg-surface-page text-ink-900", "#f6f3ee"],
          ].map(([label, classes, value]) => (
            <div className={`rounded-lg border border-slate-200 p-4 shadow-sm ${classes}`} key={label}>
              <p className="text-sm font-semibold">{label}</p>
              <p className="mt-1 text-xs opacity-80">{value}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Tipografia y jerarquias">
        <div className="space-y-3">
          <h1 className="text-3xl font-bold text-ink-900">Titulo de pagina</h1>
          <h2 className="text-lg font-semibold text-ink-900">Encabezado de seccion</h2>
          <p className="max-w-3xl text-base leading-7 text-ink-700">
            Texto principal para explicar estados, acciones y contenido operativo con una lectura sobria y profesional.
          </p>
          <p className="text-sm text-ink-500">Texto secundario para metadatos, ayuda y descripciones breves.</p>
        </div>
      </SectionCard>

      <SectionCard title="Botones e iconografia" description="Variantes base y set inicial de iconos internos.">
        <div className="flex flex-wrap gap-3">
          <Button>
            <Icon name="check" />
            Primary
          </Button>
          <Button variant="secondary">
            <Icon name="calendar" />
            Secondary
          </Button>
          <Button variant="ghost">
            <Icon name="search" />
            Ghost
          </Button>
          <Button variant="danger">
            <Icon name="logout" />
            Danger
          </Button>
          <Button isLoading>Procesando</Button>
        </div>
        <div className="mt-5 flex flex-wrap gap-4 text-brand-700">
          {(["dashboard", "calendar", "chart", "filter", "settings", "user", "users", "clock"] as const).map((name) => (
            <span className="inline-flex items-center gap-2 rounded-md bg-brand-50 px-3 py-2 text-sm font-semibold" key={name}>
              <Icon name={name} />
              {name}
            </span>
          ))}
        </div>
      </SectionCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Formularios" description="Inputs, select y textarea con foco visible.">
          <div className="space-y-4">
            <div>
              <Label htmlFor="review-name">Nombre</Label>
              <Input id="review-name" placeholder="Ej. Camila Rojas" />
            </div>
            <div>
              <Label htmlFor="review-mode">Modalidad</Label>
              <Select id="review-mode" defaultValue="online">
                <option value="online">Online</option>
                <option value="in_person">Presencial</option>
                <option value="hybrid">Hibrida</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="review-notes">Notas</Label>
              <Textarea id="review-notes" placeholder="Escribe una nota breve para revisar altura y legibilidad." />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Cards, avatar y badges">
          <Card className="space-y-4">
            <div className="flex items-center gap-3">
              <Avatar name="Sofia Morales" size="lg" />
              <div>
                <p className="font-semibold text-ink-900">Sofia Morales</p>
                <p className="text-sm text-ink-500">Psicologa clinica</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge label="Marca" />
              <Badge label="Exito" tone="success" />
              <Badge label="Pendiente" tone="warning" />
              <Badge label="Error" tone="danger" />
              <Badge label="Info" tone="info" />
              <Badge label="Neutral" tone="neutral" />
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status="pending" />
              <StatusBadge status="confirmed" />
              <StatusBadge status="cancelled" />
              <StatusBadge status="completed" />
              <StatusBadge status="no_show" />
            </div>
          </Card>
        </SectionCard>
      </div>

      <SectionCard title="Estados y helpers" description="Traducciones centralizadas, fechas es-CL y bloques de feedback.">
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="text-sm font-semibold text-ink-900">Traducciones</p>
            <dl className="mt-3 space-y-2 text-sm text-ink-700">
              <div className="flex justify-between gap-4">
                <dt>pending</dt>
                <dd>{getAppointmentStatusLabel("pending")}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt>hybrid</dt>
                <dd>{getConsultationModeLabel("hybrid")}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt>active</dt>
                <dd>{getMeetingStatusLabel("active")}</dd>
              </div>
            </dl>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="text-sm font-semibold text-ink-900">Fechas es-CL</p>
            <div className="mt-3 space-y-2 text-sm text-ink-700">
              <p>{formatLongDate(sampleDate)}</p>
              <p>{formatTime(sampleDate)}</p>
              <p>{formatDateTime(sampleDate)}</p>
            </div>
          </div>
          <div className="space-y-3">
            <LoadingState label="Cargando agenda" />
            <ErrorState title="No se pudo cargar" message="Revisa tu conexion o intenta nuevamente." />
          </div>
        </div>
        <div className="mt-4">
          <EmptyState
            title="Sin reservas para mostrar"
            description="Cuando exista informacion disponible, aparecera en este espacio con acciones claras."
            actionLabel="Buscar profesional"
            onAction={() => undefined}
          />
        </div>
      </SectionCard>
      </div>
    </main>
  );
}
