"use client";

import { useRouter, useParams } from 'next/navigation';
import { User, MapPin, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePatients } from '@/lib/hooks';

export function PatientStrip() {
  const router = useRouter();
  const params = useParams();
  const { data: patients, isLoading, error } = usePatients();
  
  const activePatientId = params.patientId as string | undefined;

  if (isLoading) {
    return (
      <div className="flex gap-3 overflow-x-auto py-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex min-w-[280px] items-center gap-3 rounded-2xl border bg-card px-4 py-3 animate-pulse"
          >
            <div className="h-10 w-10 rounded-full bg-muted" />
            <div className="flex-1 space-y-1">
              <div className="h-4 bg-muted rounded w-24" />
              <div className="h-3 bg-muted rounded w-32" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-4 text-center text-muted-foreground">
        Failed to load patients. Please try again.
      </div>
    );
  }

  if (!patients?.length) {
    return (
      <div className="py-4 text-center text-muted-foreground">
        No patients found.
      </div>
    );
  }

  return (
    <div className="flex gap-3 overflow-x-auto py-2 scrollbar-thin">
      {patients.map((patient) => (
        <button
          key={patient.id}
          onClick={() => router.push(`/patients/${patient.id}`)}
          className={cn(
            "flex min-w-[280px] items-center gap-3 rounded-2xl border bg-card px-4 py-3 text-left transition-all hover:bg-accent hover:shadow-md",
            activePatientId === patient.id && "ring-2 ring-primary shadow-lg bg-primary/5"
          )}
          aria-pressed={activePatientId === patient.id}
        >
          {/* Avatar placeholder */}
          <div className={cn(
            "flex h-10 w-10 items-center justify-center rounded-full text-white font-semibold text-sm",
            activePatientId === patient.id ? "bg-primary" : "bg-muted-foreground"
          )}>
            <User className="h-5 w-5" />
          </div>
          
          {/* Patient info */}
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm truncate">
              {patient.name}
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
              <Activity className="h-3 w-3" />
              <span className="truncate">
                {patient.preferences?.condition_focus?.join(", ") || "No conditions"}
              </span>
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              <span className="truncate">
                {patient.preferences?.preferred_location || "No location"}
              </span>
            </div>
          </div>
          
          {/* Travel indicator */}
          {patient.preferences?.willing_to_travel && (
            <div className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
              Travel OK
            </div>
          )}
        </button>
      ))}
    </div>
  );
}
