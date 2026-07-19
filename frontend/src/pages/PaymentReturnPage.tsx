import { useLocation, useNavigate } from "react-router-dom";

import { Button, PageHeader, SectionCard } from "../components/ui";

const copy = {
  success: {
    title: "Pago en verificacion",
    message: "Mercado Pago retorno con resultado exitoso. RealMeet confirmara el estado consultando el backend y los webhooks.",
  },
  pending: {
    title: "Pago pendiente",
    message: "El pago aun esta en proceso. Revisa el estado actualizado desde tus pagos.",
  },
  failure: {
    title: "Pago no completado",
    message: "Mercado Pago indico que el pago no se completo. La reserva solo cambiara cuando RealMeet verifique el estado real.",
  },
};

export function PaymentReturnPage({ result }: { result: "success" | "pending" | "failure" }) {
  const location = useLocation();
  const navigate = useNavigate();
  const content = copy[result];
  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-10">
      <PageHeader title={content.title} description="La fuente de verdad es RealMeet despues de consultar Mercado Pago." />
      <SectionCard title="Resultado del checkout">
        <p className="text-sm text-ink-600">{content.message}</p>
        {location.search ? <p className="mt-3 text-xs text-ink-500">Referencia de retorno recibida.</p> : null}
        <div className="mt-4">
          <Button onClick={() => navigate("/dashboard/payments")}>Ver mis pagos</Button>
        </div>
      </SectionCard>
    </div>
  );
}
