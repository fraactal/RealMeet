import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAvailabilityBlock,
  createAvailabilityRule,
  deleteAvailabilityBlock,
  deleteAvailabilityRule,
  fetchAvailabilityBlocks,
  fetchAvailabilityRules,
  updateAvailabilityBlock,
  updateAvailabilityRule,
} from "../api/queries";
import { normalizeApiError } from "../api/errors";
import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";
import type { AvailabilityBlockWrite, AvailabilityRule, AvailabilityRuleWrite } from "../types";
import { formatDateTime } from "../utils/dates";

const weekdays = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"];

export function ProfessionalAvailabilityPage() {
  const queryClient = useQueryClient();
  const rulesQuery = useQuery({ queryKey: ["availability-rules"], queryFn: fetchAvailabilityRules });
  const blocksQuery = useQuery({ queryKey: ["availability-blocks"], queryFn: fetchAvailabilityBlocks });
  const [ruleForm, setRuleForm] = useState({ weekday: "0", start_time: "09:00", end_time: "17:00" });
  const [editingRuleId, setEditingRuleId] = useState<number | null>(null);
  const [blockForm, setBlockForm] = useState({ start_datetime: "", end_datetime: "", reason: "" });
  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["availability-rules"] });
    void queryClient.invalidateQueries({ queryKey: ["availability-blocks"] });
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
