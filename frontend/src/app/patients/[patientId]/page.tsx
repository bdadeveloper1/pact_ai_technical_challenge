"use client";

import { useParams } from "next/navigation";
import { PatientStrip } from "@/components/PatientStrip";
import { ResourcesTable } from "@/components/ResourcesTable";
import { MetricsCards } from "@/components/MetricsCards";

export default function PatientPage() {
  const params = useParams();
  const patientId = params.patientId as string;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-foreground">
            Diabetes & Hypertension Clinic — Trial Matching
          </h1>
          <p className="text-muted-foreground mt-1">
            EHR Document Processing & Clinical Trial Eligibility Assessment
          </p>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Business Intelligence Dashboard */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Clinical Intelligence Dashboard</h2>
          <MetricsCards />
        </section>

        {/* Patient Selection Strip */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Patient Profiles</h2>
          <PatientStrip />
        </section>

        {/* Resources Table */}
        {patientId && (
          <section>
            <h2 className="text-lg font-semibold mb-4">
              EHR Resources for Patient {patientId}
            </h2>
            <ResourcesTable patientId={patientId} />
          </section>
        )}
      </div>
    </div>
  );
}
