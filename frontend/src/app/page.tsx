"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { usePatients } from "@/lib/hooks";
import { PatientStrip } from "@/components/PatientStrip";
import { MetricsCards } from "@/components/MetricsCards";
import { Loader2, AlertCircle, Users } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { data: patients, isLoading, error } = usePatients();

  // Auto-redirect to first patient if available
  useEffect(() => {
    if (patients && patients.length > 0) {
      router.push(`/patients/${patients[0].id}`);
    }
  }, [patients, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
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
        
        <div className="container mx-auto px-4 py-12">
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-3">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="text-lg">Loading patient data...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
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
        
        <div className="container mx-auto px-4 py-12">
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-3 text-red-600">
              <AlertCircle className="h-6 w-6" />
              <div>
                <div className="text-lg font-medium">Failed to load application</div>
                <div className="text-sm text-red-500">Please ensure the backend is running on port 8000</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
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

        {/* Patient Selection */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Patient Profiles</h2>
          <PatientStrip />
        </section>

        {/* Instructions */}
        <section className="text-center py-12">
          <Users className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-medium text-muted-foreground mb-2">
            Select a patient to view their EHR resources
          </h3>
          <p className="text-muted-foreground">
            Click on any patient card above to explore their clinical documents and trial matching data
          </p>
        </section>
      </div>
    </div>
  );
}
