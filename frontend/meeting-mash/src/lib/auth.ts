import NextAuth from "next-auth"
import { PrismaAdapter } from "@auth/prisma-adapter"
import { PrismaClient } from "@prisma/client"
import Credentials from "next-auth/providers/credentials"
import GitHub from "next-auth/providers/github"
import { signInSchema } from "@/lib/zod"
// Simple password hashing (replace with proper bcrypt in production)
function saltAndHashPassword(password: string): string {
  return btoa(password) // Base64 encoding - NOT secure for production!
}
 
const prisma = new PrismaClient()
 
export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: PrismaAdapter(prisma),
  session: { strategy: "jwt" },
  providers: [
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID ?? "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET ?? "",
    }),
    Credentials({
      // You can specify which fields should be submitted, by adding keys to the `credentials` object.
      // e.g. domain, username, password, 2FA token, etc.
      credentials: {
        email: {},
        password: {},
      },
      authorize: async (credentials) => {
        let user = null
        
        // Basic validation without Zod schema for login
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password are required")
        }
        
        const email = credentials.email as string
        const password = credentials.password as string
        
        // logic to salt and hash password
        const pwHash = saltAndHashPassword(password)
 
        // logic to verify if the user exists
        user = await prisma.user.findUnique({
          where: { email }
        })
 
        if (!user) {
          // No user found, so this is their first attempt to login
          // Optionally, this is also the place you could do a user registration
          throw new Error("Invalid credentials.")
        }
        
        // Check if password matches (compare hashed passwords)
        if (user.password !== pwHash) {
          throw new Error("Invalid credentials.")
        }
 
        // return user object with their profile data
        return user
      },
    }),
  ],
})