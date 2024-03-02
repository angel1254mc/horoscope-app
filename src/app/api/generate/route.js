import { NextRequest } from "next/server"

/**
 * @brief Handles creating the video, sending it back to client as blob
 * 
 * At a very high level, the pipeline works as follows
 * 
 * 1) Receive User-specified Zodiac Sign 
 * 2) Ping Daily Horoscope API for daily horoscope message
 * 3) Retrieve Random Video as Background (unless URL is provided)
 * 4) Create Video
 * @param {} request 
 * @returns 
 */
export async function POST(request) {
    const body = await request.json();

   
    return Response.json(body);
  }