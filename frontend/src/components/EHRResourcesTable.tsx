import React from "react";
import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  ChevronDown, 
  ChevronRight, 
  Info, 
  Database, 
  Sparkles, 
  Target,
  RefreshCw,
  TrendingUp 
} from "lucide-react";
import { cn } from "@/lib/utils";
import { apiClient, queryKeys } from "@/lib/api";
import { EHRResourceJson } from "@/lib/types";

/**
 * Processing state type matching backend
 */
export type ProcessingState =
  | "PROCESSING_STATE_UNSPECIFIED"
  | "PROCESSING_STATE_NOT_STARTED"
  | "PROCESSING_STATE_PROCESSING"
  | "PROCESSING_STATE_COMPLETED"
  | "PROCESSING_STATE_FAILED";

/**
 * Medallion layer indicator for enhanced visualization
 */
interface MedallionData {
  bronzeDocuments: number;
  silverEntities: number;
  goldProfiles: number;
  avgEntityConfidence: number;
  avgBusinessValue: number;
}

/**
 * Little helpers
 */
function timeAgo(iso: string | undefined) {
  if (!iso) return "—";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function StateBadge({ state }: { state: ProcessingState | number }) {
  // Convert numeric state to string if needed
  const stateStr = typeof state === 'number' ? 
    ['UNSPECIFIED', 'NOT_STARTED', 'PROCESSING', 'COMPLETED', 'FAILED'][state] || 'UNKNOWN' :
    state.replace('PROCESSING_STATE_', '');

  const map: Record<string, string> = {
    UNSPECIFIED: "bg-gray-200 text-gray-800",
    NOT_STARTED: "bg-slate-200 text-slate-800",
    PROCESSING: "bg-blue-200 text-blue-800",
    COMPLETED: "bg-green-200 text-green-800",
    FAILED: "bg-red-200 text-red-800",
  };
  
  return (
    <Badge className={cn("rounded-full", map[stateStr] || "bg-gray-200 text-gray-800")}>
      {stateStr}
    </Badge>
  );
}

function MedallionLayerBadge({ layer }: { layer: 'bronze' | 'silver' | 'gold' }) {
  const configs = {
    bronze: { icon: Database, color: "bg-amber-100 text-amber-800", label: "Bronze" },
    silver: { icon: Sparkles, color: "bg-gray-100 text-gray-800", label: "Silver" },
    gold: { icon: Target, color: "bg-yellow-100 text-yellow-800", label: "Gold" }
  };
  
  const config = configs[layer];
  const Icon = config.icon;
  
  return (
    <Badge className={cn("rounded-full gap-1", config.color)}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  );
}

/**
 * Enhanced EHR Resources Table with Medallion Architecture Integration
 */
export default function EHRResourcesTable({
  title = "EHR Document Processing Pipeline",
}: {
  title?: string;
}) {
  const [globalFilter, setGlobalFilter] = useState("");
  const [stateFilter, setStateFilter] = useState<string[]>([]);
  const [typeFilter, setTypeFilter] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const queryClient = useQueryClient();

  // Fetch resources from our Python backend
  const {
    data: resourcesResponse,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: queryKeys.resources({ limit: 100 }),
    queryFn: () => apiClient.getResources({ limit: 100 }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch medallion pipeline stats
  const { data: pipelineStats } = useQuery({
    queryKey: ['medallion', 'stats'],
    queryFn: () => fetch('http://localhost:8000/api/medallion/pipeline-stats').then(r => r.json()),
    refetchInterval: 30000,
  });

  const resources = resourcesResponse?.resources || [];

  // Columns with enhanced metadata
  const columns = useMemo<ColumnDef<EHRResourceJson>[]>(
    () => [
      {
        id: "expander",
        header: "",
        cell: ({ row }) => {
          const uid = row.original.metadata.identifier.uid;
          const isOpen = !!expanded[uid];
          return (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded((prev) => ({ ...prev, [uid]: !prev[uid] }))}
              aria-label={isOpen ? "Collapse" : "Expand"}
            >
              {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          );
        },
        size: 40,
      },
      {
        accessorKey: "metadata.identifier.patientId",
        header: "Patient",
        cell: ({ row }) => (
          <div className="font-mono text-sm">
            {row.original.metadata.identifier.patientId}
          </div>
        ),
      },
      {
        accessorKey: "metadata.resourceType",
        header: "Document Type",
        cell: ({ row }) => (
          <div className="flex flex-col gap-1">
            <span className="font-medium">{row.original.metadata.resourceType}</span>
            <MedallionLayerBadge layer="bronze" />
          </div>
        ),
      },
      {
        accessorKey: "metadata.state",
        header: "Processing State",
        cell: ({ row }) => <StateBadge state={row.original.metadata.state} />,
      },
      {
        accessorKey: "metadata.createdTime",
        header: "Created",
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium">{timeAgo(row.original.metadata.createdTime)}</span>
            <span className="text-xs text-muted-foreground">
              {new Date(row.original.metadata.createdTime).toLocaleDateString()}
            </span>
          </div>
        ),
      },
      {
        id: "aiSummary",
        header: "AI Analysis",
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            {row.original.aiSummary ? (
              <>
                <MedallionLayerBadge layer="silver" />
                <TrendingUp className="h-4 w-4 text-green-600" />
              </>
            ) : (
              <span className="text-xs text-muted-foreground">Processing...</span>
            )}
          </div>
        ),
      },
      {
        accessorKey: "metadata.identifier.uid",
        header: "UID",
        cell: ({ row }) => (
          <span className="font-mono text-xs">{row.original.metadata.identifier.uid}</span>
        ),
      },
    ],
    [expanded]
  );

  // Client-side filtering
  const filteredData = useMemo(() => {
    return resources.filter((item) => {
      const text = `${item.metadata.identifier.patientId} ${item.metadata.resourceType} ${item.humanReadableStr} ${item.aiSummary || ""}`.toLowerCase();
      const matchesGlobal = globalFilter ? text.includes(globalFilter.toLowerCase()) : true;
      
      // Convert numeric state for filtering
      const stateStr = typeof item.metadata.state === 'number' ? 
        ['UNSPECIFIED', 'NOT_STARTED', 'PROCESSING', 'COMPLETED', 'FAILED'][item.metadata.state] || 'UNKNOWN' :
        item.metadata.state.replace('PROCESSING_STATE_', '');
      
      const matchesState = stateFilter.length ? stateFilter.includes(stateStr) : true;
      const matchesType = typeFilter.length ? typeFilter.includes(item.metadata.resourceType) : true;
      return matchesGlobal && matchesState && matchesType;
    });
  }, [resources, globalFilter, stateFilter, typeFilter]);

  const table = useReactTable({
    data: filteredData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  });

  // Unique filter values
  const stateOptions = useMemo(() => {
    return Array.from(new Set(resources.map((d) => {
      return typeof d.metadata.state === 'number' ? 
        ['UNSPECIFIED', 'NOT_STARTED', 'PROCESSING', 'COMPLETED', 'FAILED'][d.metadata.state] || 'UNKNOWN' :
        d.metadata.state.replace('PROCESSING_STATE_', '');
    })));
  }, [resources]);

  const typeOptions = useMemo(
    () => Array.from(new Set(resources.map((d) => d.metadata.resourceType))),
    [resources]
  );

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              Failed to load EHR resources. Please ensure the backend is running on port 8000.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Medallion Architecture Stats */}
      {pipelineStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-amber-600" />
                <div>
                  <div className="text-2xl font-bold">{pipelineStats.storage_stats?.bronze_documents || 0}</div>
                  <div className="text-sm text-muted-foreground">Bronze Documents</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-gray-600" />
                <div>
                  <div className="text-2xl font-bold">{pipelineStats.storage_stats?.silver_entities || 0}</div>
                  <div className="text-sm text-muted-foreground">Silver Entities</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-yellow-600" />
                <div>
                  <div className="text-2xl font-bold">{pipelineStats.storage_stats?.gold_profiles || 0}</div>
                  <div className="text-sm text-muted-foreground">Gold Profiles</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <div>
                  <div className="text-2xl font-bold">
                    {Math.round((pipelineStats.data_quality?.avg_business_value || 0) * 100)}%
                  </div>
                  <div className="text-sm text-muted-foreground">Avg Business Value</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Resources Table */}
      <Card className="shadow-sm">
        <CardHeader className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl flex items-center gap-2">
              {title}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => refetch()}
                disabled={isLoading}
              >
                <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
              </Button>
            </CardTitle>
            <div className="text-sm text-muted-foreground flex items-center gap-2">
              <Info className="h-4 w-4" />
              <span>{resources.length} resources</span>
            </div>
          </div>
          
          {/* Filters */}
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="Search patient, type, content…"
              className="max-w-sm"
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
            />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2">
                  State {stateFilter.length > 0 && `(${stateFilter.length})`}
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                {stateOptions.map((s) => (
                  <DropdownMenuCheckboxItem
                    key={s}
                    checked={stateFilter.includes(s)}
                    onCheckedChange={(checked) =>
                      setStateFilter((prev) => (checked ? [...prev, s] : prev.filter((x) => x !== s)))
                    }
                  >
                    {s}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2">
                  Type {typeFilter.length > 0 && `(${typeFilter.length})`}
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                {typeOptions.map((t) => (
                  <DropdownMenuCheckboxItem
                    key={t}
                    checked={typeFilter.includes(t)}
                    onCheckedChange={(checked) =>
                      setTypeFilter((prev) => (checked ? [...prev, t] : prev.filter((x) => x !== t)))
                    }
                  >
                    {t}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>

        <CardContent>
          <div className="rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th key={header.id} className="px-3 py-3 text-left font-medium">
                        {header.isPlaceholder ? null : (
                          <div
                            className={cn(
                              header.column.getCanSort() ? "cursor-pointer select-none hover:bg-muted/50 rounded p-1" : "",
                              "flex items-center gap-1"
                            )}
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {{ asc: "▲", desc: "▼" }[header.column.getIsSorted() as string] ?? null}
                          </div>
                        )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => {
                  const uid = row.original.metadata.identifier.uid;
                  const isOpen = !!expanded[uid];
                  return (
                    <React.Fragment key={row.id}>
                      <tr className="border-b hover:bg-muted/30 transition-colors">
                        {row.getVisibleCells().map((cell) => (
                          <td key={cell.id} className="px-3 py-3 align-top">
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </td>
                        ))}
                      </tr>
                      {isOpen && (
                        <tr className="bg-muted/20">
                          <td colSpan={columns.length} className="px-6 py-4">
                            <DetailPanel item={row.original} />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="flex items-center justify-between p-4 border-t bg-background">
              <div className="text-sm text-muted-foreground">
                Showing {table.getRowModel().rows.length} of {filteredData.length} resources
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.previousPage()}
                  disabled={!table.getCanPreviousPage()}
                >
                  Previous
                </Button>
                <span className="text-sm px-2">
                  Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.nextPage()}
                  disabled={!table.getCanNextPage()}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function DetailPanel({ item }: { item: EHRResourceJson }) {
  const meta = item.metadata;
  return (
    <div className="grid md:grid-cols-3 gap-6">
      <div className="md:col-span-2 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
            <Database className="h-4 w-4" />
            Raw Document Content (Bronze Layer)
          </h3>
          <div className="bg-muted/50 rounded-lg p-3">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{item.humanReadableStr}</p>
          </div>
        </div>
        
        {item.aiSummary && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              AI-Generated Summary (Silver Layer)
            </h3>
            <div className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-3">
              <p className="text-sm leading-relaxed">{item.aiSummary}</p>
            </div>
          </div>
        )}
      </div>
      
      <div className="bg-background border rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
          <Info className="h-4 w-4" />
          Document Metadata
        </h3>
        <div className="space-y-2">
          <KV label="Patient ID" value={meta.identifier.patientId} />
          <KV label="Resource UID" value={meta.identifier.uid} />
          <KV label="Document Key" value={meta.identifier.key} />
          <KV label="Document Type" value={meta.resourceType} />
          <KV label="Processing State" value={<StateBadge state={meta.state} />} />
          <KV label="FHIR Version" value={typeof meta.version === 'number' ? `R${meta.version}` : meta.version.replace("FHIR_VERSION_", "")} />
          <KV label="Created" value={new Date(meta.createdTime).toLocaleString()} />
          <KV label="Fetched" value={new Date(meta.fetchTime).toLocaleString()} />
          <KV label="Processed" value={meta.processedTime ? new Date(meta.processedTime).toLocaleString() : "—"} />
        </div>
      </div>
    </div>
  );
}

function KV({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm py-1">
      <span className="text-muted-foreground flex-shrink-0">{label}</span>
      <span className="font-medium break-all text-right">{value}</span>
    </div>
  );
}
