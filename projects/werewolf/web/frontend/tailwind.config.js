/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        werewolf: '#dc2626',
        villager: '#16a34a',
        seer: '#7c3aed',
        witch: '#c026d3',
        hunter: '#ea580c',
        guard: '#0891b2',
      },
    },
  },
  plugins: [],
}
