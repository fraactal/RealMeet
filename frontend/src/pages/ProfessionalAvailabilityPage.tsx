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
import { Card } from "../components/ui/Card";
import type { AvailabilityBlockWrite, AvailabilityRule, AvailabilityRuleWrite } from "../types";

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Disponibilidad</h1>
        <p className="text-slate-600">Configura intervalos semanales y bloqueos manuales de tu agenda publica.</p>
      </div>

      <Card title="Reglas semanales">
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]">
          <select
            value={ruleForm.weekday}
            onChange={(event) => setRuleForm((current) => ({ ...current, weekday: event.target.value }))}
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
          >
            {weekdays.map((label, index) => (
              <option key={label} value={index}>
                {label}
              </option>
            ))}
          </select>
          <input
            type="time"
            value={ruleForm.start_time}
            onChange={(event) => setRuleForm((current) => ({ ...current, start_time: event.target.value }))}
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <input
            type="time"
            value={ruleForm.end_time}
            onChange={(event) => setRuleForm((current) => ({ ...current, end_time: event.target.value }))}
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <button className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white" onClick={saveRule}>
            {editingRuleId ? "Actualizar" : "Agregar"}
          </button>
        </div>
        {saveRuleMutation.isError ? <p className="mt-3 text-sm text-red-600">No fue posible guardar la regla.</p> : null}
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2">Dia</th>
                <th className="py-2">Inicio</th>
                <th className="py-2">Termino</th>
                <th className="py-2">Estado</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {rulesQuery.data?.map((rule) => (
                <tr key={rule.id} className="border-t border-slate-100">
                  <td className="py-3 font-medium text-slate-700">{weekdays[rule.weekday]}</td>
                  <td className="py-3 text-slate-500">{rule.start_time.slice(0, 5)}</td>
                  <td className="py-3 text-slate-500">{rule.end_time.slice(0, 5)}</td>
                  <td className="py-3 text-slate-500">{rule.is_active ? "Activa" : "Inactiva"}</td>
                  <td className="space-x-2 py-3 text-right">
                    <button className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700" onClick={() => editRule(rule)}>
                      Editar
                    </button>
                    <button className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700" onClick={() => deleteRuleMutation.mutate(rule.id)}>
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Bloqueos manuales">
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]">
          <input
            type="datetime-local"
            value={blockForm.start_datetime}
            onChange={(event) => setBlockForm((current) => ({ ...current, start_datetime: event.target.value }))}
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <input
            type="datetime-local"
            value={blockForm.end_datetime}
            onChange={(event) => setBlockForm((current) => ({ ...current, end_datetime: event.target.value }))}
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <input
            value={blockForm.reason}
            onChange={(event) => setBlockForm((current) => ({ ...current, reason: event.target.value }))}
            placeholder="Motivo opcional"
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <button
            className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
            onClick={saveBlock}
            disabled={!blockForm.start_datetime || !blockForm.end_datetime}
          >
            {editingBlockId ? "Actualizar" : "Agregar"}
          </button>
        </div>
        {saveBlockMutation.isError ? <p className="mt-3 text-sm text-red-600">No fue posible guardar el bloqueo.</p> : null}
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2">Inicio</th>
                <th className="py-2">Termino</th>
                <th className="py-2">Motivo</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {blocksQuery.data?.map((block) => (
                <tr key={block.id} className="border-t border-slate-100">
                  <td className="py-3 text-slate-600">{new Date(block.start_datetime).toLocaleString()}</td>
                  <td className="py-3 text-slate-600">{new Date(block.end_datetime).toLocaleString()}</td>
                  <td className="py-3 text-slate-500">{block.reason ?? "Sin motivo"}</td>
                  <td className="space-x-2 py-3 text-right">
                    <button
                      className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                      onClick={() => {
                        setEditingBlockId(block.id);
                        setBlockForm({
                          start_datetime: block.start_datetime.slice(0, 16),
                          end_datetime: block.end_datetime.slice(0, 16),
                          reason: block.reason ?? "",
                        });
                      }}
                    >
                      Editar
                    </button>
                    <button className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700" onClick={() => deleteBlockMutation.mutate(block.id)}>
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
