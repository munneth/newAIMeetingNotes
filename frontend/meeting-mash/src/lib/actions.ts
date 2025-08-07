"use server"

import { PrismaClient } from "@prisma/client"
import { redirect } from "next/navigation"

const prisma = new PrismaClient()

// Simple password hashing (replace with proper bcrypt in production)
function saltAndHashPassword(password: string): string {
  return btoa(password) // Base64 encoding - NOT secure for production!
}

export async function loginAction(formData: FormData) {
  // For login, we'll redirect to the NextAuth signin page
  // This avoids CSRF issues and uses NextAuth's built-in form
  redirect('/api/auth/signin?callbackUrl=/')
}

export async function signupAction(formData: FormData) {
  const email = formData.get('email') as string
  const password = formData.get('password') as string
  const confirmPassword = formData.get('confirmPassword') as string
  
  // Check if passwords match
  if (password !== confirmPassword) {
    throw new Error("Passwords do not match")
  }
  
  // Check if user already exists
  const existingUser = await prisma.user.findUnique({
    where: { email }
  })
  
  if (existingUser) {
    throw new Error("User with this email already exists")
  }
  
  // Hash the password
  const hashedPassword = saltAndHashPassword(password)
  
  // Create new user in database
  const newUser = await prisma.user.create({
    data: {
      email,
      password: hashedPassword,
    }
  })
  
  // Redirect to login after successful signup
  redirect('/login?message=Account created successfully! Please sign in.')
} 