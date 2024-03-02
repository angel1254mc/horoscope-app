"use client";
import Image from "next/image";
import { useForm } from "react-hook-form";
import * as yup from "yup";

export default function Home() {

    const signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];

    const requestSchema = yup.object({
      zodiac_sign: yup.string().required().oneOf(signs),
      daily_message: yup.string().optional(),
      bg_url: yup.string().url().optional()
    });

    const {
      register,
      handleSubmit,
      watch,
      formState: { errors }
    } = useForm();

    const onSubmit = async (payload) => {
      
      // Assume that React Hook Form checked for validity

      const response = await fetch("http://localhost:5000/api/generate_video", {
        method: "POST",
        body: JSON.stringify(payload),
      })

      const blob = await response.blob();
      const objectURL = URL.createObjectURL(blob);
      console.log(objectURL);
    }

    return (
        <main className="w-full h-[100vh] bg-black flex flex-col items-center justify-center">
            <div className="h-full flex items-center">
                <div className="bg-[#101010] w-[1200px]  max-h-[52rem] h-3/4 min-h-[36rem] flex rounded-lg border-gray-500 border-2">
                    <form onSubmit={handleSubmit(onSubmit)} className="w-full p-8">
                      <h1 className="text-3xl font-bold">Mini Horoscope Video Generator</h1>
                      <p className="text-gray-300 mt-2">Simple web-app for creating short-form daily horoscope content</p>
                      <div className="flex flex-col gap-y-2">
                        <div className="mt-2">
                          <label className="text-lg w-full" for="zodiac_sign">Zodiac Sign</label>
                          <select {...register("zodiac_sign")} className="appearance-none w-2/3 bg-transparent block border-gray-500 border-[1px] mt-2 rounded-lg px-2 py-1" name="zodiac_sign">
                            {signs.map((sign) => 
                              <option key={sign} className="appearance-none text-black">{sign}</option>
                            )}
                          </select>
                        </div>
                        <div className="mt-2">
                          <label className="text-lg w-full" for="zodiac_sign">Daily Horoscope (optional)</label>
                          <textarea {...register("daily_message")} className="appearance-none w-2/3 bg-transparent h-44 block border-gray-500 border-[1px] mt-2 rounded-lg px-2 py-1" name="zodiac_sign"/>
                        </div>
                        <div className="mt-2">
                          <label className="text-lg w-full" for="zodiac_sign">BG Video URL (optional)</label>
                          <input {...register("bg_url")}  className="appearance-none w-2/3 bg-transparent block border-gray-500 border-[1px] mt-2 rounded-lg px-2 py-1" name="zodiac_sign"/>
                        </div>
                        <div className="mt-2">
                          <button type="submit" className="px-4 py-2 bg-black rounded-md border-gray-700 border-[1px]">Generate</button>
                        </div>

                      </div>
                    </form>
                    <div className="w-[600px] border-gray-500 border-l-2 flex flex-col justify-center items-center">
                        <div className="w-[300px] aspect-[9/16]"> 
                          <video controls className="w-full h-full">
                            <source src={""}></source>
                          </video>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
