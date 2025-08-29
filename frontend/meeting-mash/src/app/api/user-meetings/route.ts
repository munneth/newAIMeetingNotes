import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function GET(request: NextRequest) {
  try {
    // Get API key from Authorization header
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ 
        error: 'Missing or invalid Authorization header. Use: Authorization: Bearer YOUR_API_KEY' 
      }, { status: 401 })
    }
    
    const apiKey = authHeader.replace('Bearer ', '')
    
    // Validate API key format (should be a secure random string)
    if (!apiKey || apiKey.length < 32) {
      return NextResponse.json({ 
        error: 'Invalid API key format' 
      }, { status: 401 })
    }
    
    // Get user ID from query parameter
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('userId')
    
    if (!userId) {
      return NextResponse.json({ 
        error: 'Missing userId parameter. Use: /api/user-meetings?userId=USER_ID' 
      }, { status: 400 })
    }
    
    // Validate API key against environment variable
    const validApiKey = process.env.USER_MEETINGS_API_KEY
    
    if (!validApiKey) {
      console.error('USER_MEETINGS_API_KEY environment variable not set')
      return NextResponse.json({ 
        error: 'Server configuration error' 
      }, { status: 500 })
    }
    
    if (apiKey !== validApiKey) {
      return NextResponse.json({ 
        error: 'Invalid API key' 
      }, { status: 401 })
    }
    
    // Verify user exists
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { id: true, email: true } // Only select necessary fields
    })
    
    if (!user) {
      return NextResponse.json({ 
        error: 'User not found' 
      }, { status: 404 })
    }
    
    // Get meetings for the specified user
    const meetings = await prisma.meeting.findMany({
      where: {
        userId: userId,
      },
      orderBy: {
        createdAt: 'desc',
      },
      select: {
        id: true,
        link: true,
        meetingId: true,
        duration: true,
        createdAt: true,
        updatedAt: true,
        // Don't include userId for security
      }
    })
    
    return NextResponse.json({ 
      success: true,
      user: {
        id: user.id,
        email: user.email
      },
      meetings,
      count: meetings.length
    })

  } catch (error) {
    console.error('Error fetching user meetings:', error)
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    )
  }
}
