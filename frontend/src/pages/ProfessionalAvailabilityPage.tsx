import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createExternalCalendar,
  createAvailabilityBlock,
  createAvailabilityRule,
  deleteAvailabilityBlock,
  deleteAvailabilityRule,
  disableExternalCalendar,
  enableExternalCalendar,
  fetchAvailabilityBlocks,
  fetchAvailabilityRules,
  fetchCalendarSyncSettings,
  fetchExternalCalendars,
  testExternalCalendar,
  updateCalendarSyncSettings,
  updateAvailabilityBlock,
  updateAvailabilityRule,
} from "../api/queries";
import { normalizeApiError } from "../api/errors";
import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";
import type { AvailabilityBlockWrite, AvailabilityRule, AvailabilityRuleWrite, CalendarConflictPolicy, ExternalCalendar } from "../types";
import { formatDateTime } from "../utils/dates";

const weekdays = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"];

export function ProfessionalAvailabilityPage() {
  const queryClient = useQueryClient();
  const rulesQuery = useQuery({ queryKey: ["availability-rules"], queryFn: fetchAvailabilityRules });
  const blocksQuery = useQuery({ queryKey: ["availability-blocks"], queryFn: fetchAvailabilityBlocks });
  const calendarsQuery = useQuery({ queryKey: ["external-calendars"], queryFn: fetchExternalCalendars });
  const syncSettingsQuery = useQuery({ queryKey: ["calendar-sync-settings"], queryFn: fetchCalendarSyncSettings });
  const [ruleForm, setRuleForm] = useState({ weekday: "0", start_time: "09:00", end_time: "17:00" });
  const [editingRuleId, setEditingRuleId] = useState<number | null>(null);
  const [blockForm, setBlockForm] = useState({ start_datetime: "", end_datetime: "", reason: "" });
  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);
  const [calendarForm, setCalendarForm] = useState({ external_calendar_id: "fake-primary", name: "Calendario fake principal", timezone: "America/Santiago" });
  const [calendarTestMessage, setCalendarTestMessage] = useState("");

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["availability-rules"] });
    void queryClient.invalidateQueries({ queryKey: ["availability-blocks"] });
  };
  const refreshCalendars = () => {
    void queryClient.invalidateQueries({ queryKey: ["external-calendars"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-sync-settings"] });
  };

  const saveRuleMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number | null; payload: AvailabilityRuleWrite }) =>
      id ? updateAvailabilityRule(id, payload) : createAvailabilityRule(payload),
    onSuccess: () => {
      setEditingRuleId(null);
      setRuleForm({ weekday: "0", start_time: "09:00", end_time: "17:00" });
      refresh();
    },
  });
  const deleteRuleMutation = useMutation({ mutationFn: deleteAvailabilityRule, onSuccess: refresh });
  const saveBlockMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number | null; payload: AvailabilityBlockWrite }) =>
      id ? updateAvailabilityBlock(id, payload) : createAvailabilityBlock(payload),
    onSuccess: () => {
      setEditingBlockId(null);
      setBlockForm({ start_datetime: "", end_datetime: "", reason: "" });
      refresh();
    },
  });
  const deleteBlockMutation = useMutation({ mutationFn: deleteAvailabilityBlock, onSuccess: refresh });
  const createCalendarMutation = useMutation({
    mutationFn: () =>
      createExternalCalendar({
        provider: "fake",
        external_calendar_id: calendarForm.external_calendar_id,
        name: calendarForm.name,
        timezone: calendarForm.timezone,
        description: "Calendario externo fake para pruebas locales.",
        read_enabled: true,
        write_enabled: false,
        conflict_check_enabled: true,
        is_primary: calendarsQuery.data?.length === 0,
      }),
    onSuccess: refreshCalendars,
  });
  const enableCalendarMutation = useMutation({ mutationFn: enableExternalCalendar, onSuccess: refreshCalendars });
  const disableCalendarMutation = useMutation({ mutationFn: disableExternalCalendar, onSuccess: refreshCalendars });
  const testCalendarMutation = useMutation({
    mutationFn: testExternalCalendar,
    onSuccess: (result) => {
      setCalendarTestMessage(`${result.health.message} Busy periods: ${result.busy_periods.length}. Evento fake: ${result.created_event_id ?? "sin evento"}.`);
      refreshCalendars();
    },
  });
  const updateSettingsMutation = useMutation({ mutationFn: updateCalendarSyncSettings, onSuccess: refreshCalendars });

  const saveRule = () => {
    saveRuleMutation.mutate({
      id: editingRuleId,
      payload: {
        weekday: Number(ruleForm.weekday),
        start_time: ruleForm.start_time,
        end_time: ruleForm.end_time,
        is_active: true,
      },
    });
  };

  const editRule = (rule: AvailabilityRule) => {
    setEditingRuleId(rule.id);
    setRuleForm({
      weekday: rule.weekday.toString(),
      start_time: rule.start_time.slice(0, 5),
      end_time: rule.end_time.slice(0, 5),
    });
  };

  const saveBlock = () => {
    saveBlockMutation.mutate({
      id: editingBlockId,
      payload: {
        start_datetime: new Date(blockForm.start_datetime).toISOString(),
        end_datetime: new Date(blockForm.end_datetime).toISOString(),
        reason: blockForm.reason || null,
        type: "blocked",
      },
    });
  };

  if (rulesQuery.isLoading || blocksQuery.isLoading) {
    return <LoadingState label="Cargando disponibilidad" />;
  }

  if (rulesQuery.isError || blocksQuery.isError) {
    return <ErrorState title="No pudimos cargar tu disponibilidad" message="Intenta nuevamente antes de editar horarios o bloqueos." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disponibilidad"
        description="Define los horarios semanales y bloqueos que usa RealMeet para mostrar horas disponibles a clientes."
      />

      <SectionCard title="Calendarios externos" description="Fundacion para lectura futura de ocupacion externa. En esta etapa solo el proveedor fake esta operativo.">
        <p className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-ink-600">Google Calendar y Microsoft 365 estaran disponibles en proximas etapas. Esta configuracion todavia no modifica el motor real de disponibilidad.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto] md:items-end">
          <div>
            <Label htmlFor="external-calendar-id">ID externo fake</Label>
            <Input id="external-calendar-id" value={calendarForm.external_calendar_id} onChange={(event) => setCalendarForm((current) => ({ ...current, external_calendar_id: event.target.value }))} />
          </div>
          <div>
            <Label htmlFor="external-calendar-name">Nombre</Label>
            <Input id="external-calendar-name" value={calendarForm.name} onChange={(event) => setCalendarForm((current) => ({ ...current, name: event.target.value }))} />
          </div>
          <div>
            <Label htmlFor="external-calendar-timezone">Timezone</Label>
            <Input id="external-calendar-timezone" value={calendarForm.timezone} onChange={(event) => setCalendarForm((current) => ({ ...current, timezone: event.target.value }))} />
          </div>
          <Button disabled={!calendarForm.external_calendar_id || !calendarForm.name} isLoading={createCalendarMutation.isPending} onClick={() => createCalendarMutation.mutate()}>Registrar fake</Button>
        </div>
        {createCalendarMutation.isError ? <ErrorState message={normalizeApiError(createCalendarMutation.error).message} title="No se pudo registrar el calendario" /> : null}
        <div className="mt-5 grid gap-3 lg:grid-cols-2">
          {calendarsQuery.isLoading ? <LoadingState label="Cargando calendarios externos" /> : null}
          {calendarsQuery.data?.map((calendar) => (
            <ExternalCalendarCard
              calendar={calendar}
              key={calendar.id}
              onDisable={() => disableCalendarMutation.mutate(calendar.id)}
              onEnable={() => enableCalendarMutation.mutate(calendar.id)}
              onTest={() => testCalendarMutation.mutate(calendar.id)}
              busy={enableCalendarMutation.isPending || disableCalendarMutation.isPending || testCalendarMutation.isPending}
            />
          ))}
          {!calendarsQuery.isLoading && calendarsQuery.data?.length === 0 ? <EmptyState title="Sin calendarios externos" description="Registra un calendario fake para validar la fundacion del dominio." /> : null}
        </div>
        {calendarTestMessage ? <p className="mt-4 rounded-md border border-success-200 bg-success-50 p-3 text-sm text-success-700">{calendarTestMessage}</p> : null}
        {syncSettingsQuery.data ? (
          <div className="mt-5 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-[1fr_1fr_1fr_auto] md:items-end">
            <label className="flex items-center gap-2 text-sm font-semibold text-ink-700">
              <input
                checked={syncSettingsQuery.data.sync_enabled}
                onChange={(event) => updateSettingsMutation.mutate({ sync_enabled: event.target.checked })}
                type="checkbox"
              />
              Sincronizacion habilitada
            </label>
            <div>
              <Label htmlFor="calendar-policy">Politica</Label>
              <Select
                id="calendar-policy"
                value={syncSettingsQuery.data.conflict_policy}
                onChange={(event) => updateSettingsMutation.mutate({ conflict_policy: event.target.value as CalendarConflictPolicy })}
              >
                <option value="internal_only">Solo disponibilidad interna</option>
                <option value="external_busy_blocks">Bloques ocupados externos</option>
                <option value="disabled">Deshabilitada</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="lookahead-days">Dias hacia adelante</Label>
              <Input
                id="lookahead-days"
                max={365}
                min={1}
                type="number"
                value={syncSettingsQuery.data.lookahead_days}
                onChange={(event) => updateSettingsMutation.mutate({ lookahead_days: Number(event.target.value) })}
              />
            </div>
            <Badge label="Persistido para etapas futuras" tone="info" />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard title="Reglas semanales" description="Agrega los dias y horarios en que atiendes de forma recurrente.">
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto] md:items-end">
          <div>
            <Label htmlFor="rule-weekday">Dia</Label>
            <Select
              id="rule-weekday"
            value={ruleForm.weekday}
            onChange={(event) => setRuleForm((current) => ({ ...current, weekday: event.target.value }))}
          >
            {weekdays.map((label, index) => (
              <option key={label} value={index}>
                {label}
              </option>
            ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="rule-start">Inicio</Label>
            <Input
              id="rule-start"
              type="time"
              value={ruleForm.start_time}
              onChange={(event) => setRuleForm((current) => ({ ...current, start_time: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="rule-end">Termino</Label>
            <Input
              id="rule-end"
              type="time"
              value={ruleForm.end_time}
              onChange={(event) => setRuleForm((current) => ({ ...current, end_time: event.target.value }))}
            />
          </div>
          <Button isLoading={saveRuleMutation.isPending} onClick={saveRule}>
            {editingRuleId ? "Actualizar" : "Agregar"}
          </Button>
        </div>
        {saveRuleMutation.isError ? <ErrorState message={normalizeApiError(saveRuleMutation.error).message} title="No se pudo guardar la regla" /> : null}
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {rulesQuery.data?.map((rule) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={rule.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-ink-900">{weekdays[rule.weekday]}</p>
                  <p className="mt-1 text-sm text-ink-500">
                    {rule.start_time.slice(0, 5)} - {rule.end_time.slice(0, 5)}
                  </p>
                </div>
                <Badge label={rule.is_active ? "Activa" : "Inactiva"} tone={rule.is_active ? "success" : "neutral"} />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={() => editRule(rule)} size="sm" variant="secondary">
                  Editar
                </Button>
                <Button disabled={deleteRuleMutation.isPending} onClick={() => deleteRuleMutation.mutate(rule.id)} size="sm" variant="danger">
                  Eliminar
                </Button>
              </div>
            </div>
          ))}
          {rulesQuery.data?.length === 0 ? (
            <div className="md:col-span-2 xl:col-span-3">
              <EmptyState title="Sin reglas semanales" description="Agrega al menos un horario para que los clientes puedan encontrar horas disponibles." />
            </div>
          ) : null}
        </div>
      </SectionCard>

      <SectionCard title="Bloqueos manuales" description="Registra excepciones para fechas u horarios que no quieres mostrar disponibles.">
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto] md:items-end">
          <div>
            <Label htmlFor="block-start">Inicio</Label>
            <Input
              id="block-start"
              type="datetime-local"
              value={blockForm.start_datetime}
              onChange={(event) => setBlockForm((current) => ({ ...current, start_datetime: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="block-end">Termino</Label>
            <Input
              id="block-end"
              type="datetime-local"
              value={blockForm.end_datetime}
              onChange={(event) => setBlockForm((current) => ({ ...current, end_datetime: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="block-reason">Motivo opcional</Label>
            <Input
              id="block-reason"
              value={blockForm.reason}
              onChange={(event) => setBlockForm((current) => ({ ...current, reason: event.target.value }))}
              placeholder="Ej. reunion externa"
            />
          </div>
          <Button
            isLoading={saveBlockMutation.isPending}
            onClick={saveBlock}
            disabled={!blockForm.start_datetime || !blockForm.end_datetime}
          >
            {editingBlockId ? "Actualizar" : "Agregar"}
          </Button>
        </div>
        {saveBlockMutation.isError ? <ErrorState message={normalizeApiError(saveBlockMutation.error).message} title="No se pudo guardar el bloqueo" /> : null}
        <div className="mt-5 grid gap-3 lg:grid-cols-2">
          {blocksQuery.data?.map((block) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={block.id}>
              <p className="font-semibold text-ink-900">{formatDateTime(block.start_datetime)}</p>
              <p className="mt-1 text-sm text-ink-500">Hasta {formatDateTime(block.end_datetime)}</p>
              <p className="mt-3 text-sm text-ink-700">{block.reason ?? "Sin motivo informado"}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button
                  onClick={() => {
                    setEditingBlockId(block.id);
                    setBlockForm({
                      start_datetime: block.start_datetime.slice(0, 16),
                      end_datetime: block.end_datetime.slice(0, 16),
                      reason: block.reason ?? "",
                    });
                  }}
                  size="sm"
                  variant="secondary"
                >
                  Editar
                </Button>
                <Button disabled={deleteBlockMutation.isPending} onClick={() => deleteBlockMutation.mutate(block.id)} size="sm" variant="danger">
                  Eliminar
                </Button>
              </div>
            </div>
          ))}
          {blocksQuery.data?.length === 0 ? (
            <div className="lg:col-span-2">
              <EmptyState title="Sin bloqueos manuales" description="No tienes excepciones creadas para tu agenda." />
            </div>
          ) : null}
        </div>
      </SectionCard>
    </div>
  );
}

function ExternalCalendarCard({ calendar, busy, onDisable, onEnable, onTest }: { calendar: ExternalCalendar; busy: boolean; onDisable: () => void; onEnable: () => void; onTest: () => void }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-ink-900">{calendar.name}</p>
          <p className="mt-1 text-sm text-ink-500">{calendar.provider} · {calendar.external_calendar_id}</p>
        </div>
        <Badge label={calendar.enabled ? "Habilitado" : "Deshabilitado"} tone={calendar.enabled ? "success" : "neutral"} />
      </div>
      <div className="mt-3 grid gap-2 text-sm text-ink-600 sm:grid-cols-2">
        <p>Zona: {calendar.timezone}</p>
        <p>Estado: {calendar.sync_status}</p>
        <p>Lectura: {calendar.read_enabled ? "Activa" : "Inactiva"}</p>
        <p>Conflictos: {calendar.conflict_check_enabled ? "Activos" : "Inactivos"}</p>
        <p>Escritura futura: {calendar.write_enabled ? "Marcada" : "No marcada"}</p>
        <p>Primario: {calendar.is_primary ? "Si" : "No"}</p>
      </div>
      {calendar.last_sync_error_code ? <p className="mt-3 text-sm text-danger-700">Error resumido: {calendar.last_sync_error_code}</p> : null}
      <div className="mt-4 flex flex-wrap gap-2">
        {calendar.enabled ? <Button isLoading={busy} onClick={onDisable} size="sm" variant="secondary">Deshabilitar</Button> : <Button isLoading={busy} onClick={onEnable} size="sm">Habilitar</Button>}
        <Button isLoading={busy} onClick={onTest} size="sm" variant="secondary">Probar fake</Button>
      </div>
    </article>
  );
}
