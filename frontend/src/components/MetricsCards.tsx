"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Heart, Activity, TrendingUp, Stethoscope, Calendar } from "lucide-react";
import { usePipelineStats, usePatients } from "@/lib/hooks";

export function MetricsCards() {
  const { data: stats, isLoading: statsLoading } = usePipelineStats();
  const { data: patients, isLoading: patientsLoading } = usePatients();

  if (statsLoading || patientsLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="animate-pulse">
                <div className="h-4 bg-muted rounded w-16 mb-2" />
                <div className="h-8 bg-muted rounded w-12" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats || !patients) return null;

  // Calculate business metrics
  const totalPatients = patients.length;
  const diabetesPatients = patients.filter(p => 
    p.preferences?.condition_focus?.some(c => c.includes('diabetes'))
  ).length;
  const trialEligiblePatients = stats.storage_stats.gold_profiles;
  const avgTrialMatchScore = Math.round(stats.data_quality.avg_business_value * 100);

  const businessMetrics = [
    {
      icon: Users,
      label: "Total Patients",
      value: totalPatients,
      color: "text-blue-600",
      description: "Active patient profiles"
    },
    {
      icon: Heart,
      label: "Diabetes Patients", 
      value: diabetesPatients,
      color: "text-red-600",
      description: "Patients with diabetes focus"
    },
    {
      icon: Activity,
      label: "Trial Eligible",
      value: trialEligiblePatients,
      color: "text-green-600", 
      description: "Ready for trial matching"
    },
    {
      icon: TrendingUp,
      label: "Match Score",
      value: `${avgTrialMatchScore}%`,
      color: "text-purple-600",
      description: "Average trial compatibility"
    }
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {businessMetrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.label}>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Icon className={`h-5 w-5 ${metric.color}`} />
                  <div>
                    <div className="text-2xl font-bold">{metric.value}</div>
                    <div className="text-sm text-muted-foreground">{metric.label}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      {/* Top Clinical Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Stethoscope className="h-5 w-5" />
            Clinical Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-2">Top Conditions</h4>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Type 2 Diabetes</span>
                  <span className="font-medium">{diabetesPatients}/{totalPatients}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Hypertension</span>
                  <span className="font-medium">{patients.filter(p => 
                    p.preferences?.condition_focus?.some(c => c.includes('hypertension'))
                  ).length}/{totalPatients}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Cardiovascular Disease</span>
                  <span className="font-medium">{patients.filter(p => 
                    p.preferences?.condition_focus?.some(c => c.includes('cardiovascular'))
                  ).length}/{totalPatients}</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-2">Trial Readiness</h4>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Travel Willing</span>
                  <span className="font-medium">{patients.filter(p => p.preferences?.willing_to_travel).length}/{totalPatients}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Consent Given</span>
                  <span className="font-medium">{patients.filter(p => p.consentGiven).length}/{totalPatients}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Phase III Preferred</span>
                  <span className="font-medium">{patients.filter(p => 
                    p.preferences?.trial_phase_preference?.includes('Phase III')
                  ).length}/{totalPatients}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
