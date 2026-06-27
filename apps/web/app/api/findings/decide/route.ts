import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { id, decision } = body;

        if (!id || !["approved", "rejected"].includes(decision)) {
            return NextResponse.json(
                { error: "Invalid payload. Required: id (uuid), decision (approved|rejected)" },
                { status: 400 }
            );
        }

        const { error: reviewError } = await supabase
            .from("reviews")
            .insert({
                finding_id: id,
                reviewer_id: "fabio.jorge",
                decision: decision,
            });

        if (reviewError) {
            return NextResponse.json({ error: reviewError.message }, { status: 500 });
        }

        const newStatus = decision === "approved" ? "reviewed" : "discarded";
        const { error: updateError } = await supabase
            .from("findings")
            .update({ status: newStatus })
            .eq("id", id);

        if (updateError) {
            return NextResponse.json({ error: updateError.message }, { status: 500 });
        }

        return NextResponse.json({ ok: true, id, decision, newStatus });
    } catch (error) {
        return NextResponse.json(
            { error: "Invalid request", details: String(error) },
            { status: 400 }
        );
    }
}
