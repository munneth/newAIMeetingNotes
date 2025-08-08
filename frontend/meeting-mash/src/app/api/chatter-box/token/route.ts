import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Make request to Chatter Box auth endpoint
    const response = await fetch("https://bot.chatter-box.io/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.CHATTER_BOX_TOKEN}`,
      },
      body: JSON.stringify({
        expiresIn: body.expiresIn || 7200,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chatter Box API error: ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Chatter Box auth error:", error);
    return NextResponse.json(
      { error: "Authentication failed" },
      { status: 500 },
    );
  }
}
