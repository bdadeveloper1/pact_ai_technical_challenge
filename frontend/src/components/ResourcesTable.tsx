"use client";

import React from "react";
import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { ColumnDef, flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, useReactTable, } from "@tanstack/react-table";
import { Card, CardContent, CardHeader, CardTitle, } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuTrigger, } from "@/components/ui/dropdown-menu";
import { ChevronDown, ChevronRight, Info, Loader2, AlertCircle, FileText, Sparkles } from "lucide-react";
import { cn, relative, formatDateTime } from "@/lib/utils";
import { useResources, useResourceDetail, usePrefetchResource } from "@/lib/hooks";
import type { ProcessingState, EHRResourceJson } from "@/lib/types";

function StateBadge({ state }: { state: ProcessingState | number }) {
  const stateStr = typeof state === 'string' 
    ? state.replace("PROCESSING_STATE_", "")
    : ['UNSPECIFIED', 'NOT_STARTED', 'PROCESSING', 'COMPLETED', 'FAILED'][state as number] || 'UNKNOWN';
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

interface ResourcesTableProps {
  patientId: string;
}

export function ResourcesTable({ patientId }: ResourcesTableProps) {
  const [globalFilter, setGlobalFilter] = useState("");
  const [stateFilter, setStateFilter] = useState<string[]>([]);
  const [typeFilter, setTypeFilter] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  
  const prefetchResource = usePrefetchResource();
  const { data: resources = [], isLoading, error } = useResources(patientId);

  // Columns definition matching the spec
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
              aria-expanded={isOpen}
            >
              {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          );
        },
        size: 50,
      },
      {
        accessorKey: "metadata.resourceType",
        header: "Resource Type",
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">{row.original.metadata.resourceType}</span>
          </div>
        ),
      },
      {
        accessorKey: "metadata.state",
        header: "State",
        cell: ({ row }) => <StateBadge state={row.original.metadata.state} />,
      },
      {
        accessorKey: "metadata.createdTime",
        header: "Created",
        cell: ({ row }) => {
          const time = row.original.metadata.createdTime;
          return (
            <div className="flex flex-col">
              <span className="font-medium">{relative(time)}</span>
              <span className="text-xs text-muted-foreground" title={formatDateTime(time)}>
                {formatDateTime(time)}
              </span>
            </div>
          );
        },
      },
      {
        accessorKey: "metadata.fetchTime", 
        header: "Fetched",
        cell: ({ row }) => {
          const time = row.original.metadata.fetchTime;
          return (
            <div className="flex flex-col">
              <span className="font-medium">{relative(time)}</span>
              <span className="text-xs text-muted-foreground" title={formatDateTime(time)}>
                {formatDateTime(time)}
              </span>
            </div>
          );
        },
      },
      {
        accessorKey: "metadata.identifier.uid",
        header: "UID",
        cell: ({ row }) => (
          <span className="font-mono text-xs text-muted-foreground">
            {row.original.metadata.identifier.uid}
          </span>
        ),
      },
    ],
    [expanded]
  );

  // Client-side filtering
  const filteredData = useMemo(() => {
    return resources.filter((item) => {
      const text = `${item.metadata.resourceType} ${item.humanReadableStr} ${item.aiSummary || ""}`.toLowerCase();
      const matchesGlobal = globalFilter ? text.includes(globalFilter.toLowerCase()) : true;
      
      const stateStr = typeof item.metadata.state === 'string' 
        ? item.metadata.state.replace("PROCESSING_STATE_", "")
        : ['UNSPECIFIED', 'NOT_STARTED', 'PROCESSING', 'COMPLETED', 'FAILED'][item.metadata.state] || 'UNKNOWN';
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
      pagination: { pageSize: 10 },
      sorting: [{ id: "metadata.createdTime", desc: true }],
    },
  });

  // Filter options
  const stateOptions = useMemo(() => {
    return Array.from(new Set(resources.map((d) => 
      typeof d.metadata.state === 'string' 
        ? d.metadata.state.replace("PROCESSING_STATE_", "")
        : ['UNSPECIFIED', 'NOT_STARTED', 'PROCESSING', 'COMPLETED', 'FAILED'][d.metadata.state] || 'UNKNOWN'
    )));
  }, [resources]);

  const typeOptions = useMemo(() => {
    return Array.from(new Set(resources.map((d) => d.metadata.resourceType)));
  }, [resources]);

  // Loading state
  if (isLoading) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading resources...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 bg-muted rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="shadow-sm border-red-200">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <div>
              <div className="font-medium">Failed to load resources</div>
              <div className="text-sm text-red-500">Please try again later</div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!resources.length) {
    return (
      <Card className="shadow-sm">
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
            <div className="text-lg font-medium text-muted-foreground">No resources yet</div>
            <div className="text-sm text-muted-foreground">This patient has no EHR resources to display</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="space-y-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">EHR Resources</CardTitle>
          <div className="text-sm text-muted-foreground flex items-center gap-2">
            <Info className="h-4 w-4" />
            <span>{resources.length} resources</span>
          </div>
        </div>
        
        {/* Toolbar */}
        <div className="flex flex-wrap gap-2">
          <Input
            placeholder="Search resources, content..."
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
              {stateOptions.map((state) => (
                <DropdownMenuCheckboxItem
                  key={state}
                  checked={stateFilter.includes(state)}
                  onCheckedChange={(checked) =>
                    setStateFilter((prev) => (checked ? [...prev, state] : prev.filter((x) => x !== state)))
                  }
                >
                  {state}
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
              {typeOptions.map((type) => (
                <DropdownMenuCheckboxItem
                  key={type}
                  checked={typeFilter.includes(type)}
                  onCheckedChange={(checked) =>
                    setTypeFilter((prev) => (checked ? [...prev, type] : prev.filter((x) => x !== type)))
                  }
                >
                  {type}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent>
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="px-4 py-3 text-left font-medium">
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
                    <tr 
                      className="border-b hover:bg-muted/30 transition-colors"
                      onMouseEnter={() => prefetchResource(patientId, uid)}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className="px-4 py-3 align-top">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                    {isOpen && (
                      <tr className="bg-muted/20">
                        <td colSpan={columns.length} className="px-6 py-4">
                          <ResourceDetailPanel patientId={patientId} uid={uid} />
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
  );
}

function ResourceDetailPanel({ patientId, uid }: { patientId: string; uid: string }) {
  const { data: resource, isLoading, error } = useResourceDetail(patientId, uid, true);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Loading details...</span>
      </div>
    );
  }

  if (error || !resource) {
    return (
      <div className="flex items-center gap-2 py-4 text-red-600">
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm">Failed to load resource details</span>
      </div>
    );
  }

  const meta = resource.metadata;

  return (
    <div className="grid md:grid-cols-3 gap-6">
      {/* Content */}
      <div className="md:col-span-2 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Human-readable Content
          </h3>
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{resource.humanReadableStr}</p>
          </div>
        </div>
        
        {resource.aiSummary && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              AI Summary
            </h3>
            <div className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-4">
              <p className="text-sm leading-relaxed">{resource.aiSummary}</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Metadata */}
      <div className="bg-background border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
          <Info className="h-4 w-4" />
          Metadata
        </h3>
        <div className="space-y-2">
          <KV label="Patient ID" value={meta.identifier.patientId} />
          <KV label="UID" value={meta.identifier.uid} />
          <KV label="Key" value={meta.identifier.key} />
          <KV label="Type" value={meta.resourceType} />
          <KV label="State" value={<StateBadge state={meta.state} />} />
          <KV label="FHIR Version" value={
            typeof meta.version === 'string' 
              ? meta.version.replace("FHIR_VERSION_", "")
              : `R${meta.version}` || 'Unknown'
          } />
          <KV label="Created" value={formatDateTime(meta.createdTime)} />
          <KV label="Fetched" value={formatDateTime(meta.fetchTime)} />
          <KV label="Processed" value={meta.processedTime ? formatDateTime(meta.processedTime) : "—"} />
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
