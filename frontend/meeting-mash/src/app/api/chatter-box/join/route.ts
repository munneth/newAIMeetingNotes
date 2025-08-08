import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const response = await fetch('https://bot.chatter-box.io/join', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.CHATTER_BOX_TOKEN}`
            },
            body: JSON.stringify(body)
        })
        
        if (!response.ok) {
            throw new Error(`Chatter Box API error: ${response.status}`)
        }
        
        const data = await response.json()
        return NextResponse.json(data)
        
    } catch (error) {
        console.error('Chatter Box join error:', error)
        return NextResponse.json(
            { error: 'Join failed' },
            { status: 500 }
        )
    }
}