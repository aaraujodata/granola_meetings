import { z } from "zod";
import { zColor } from "@remotion/zod-types";

export const promoVideoSchema = z.object({
  title: z.string().default("Granola Meeting Explorer"),
  tagline: z.string().default("Export \u00b7 Index \u00b7 Search \u00b7 Enrich"),
  meetingCount: z.number().default(573),
  searchEntries: z.number().default(1165),
  exportedCount: z.number().default(573),
  searchQuery: z.string().default("action items from Q4"),
  accentColor: zColor().default("#2563eb"),
});

export type PromoVideoProps = z.infer<typeof promoVideoSchema>;
