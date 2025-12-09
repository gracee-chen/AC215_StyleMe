# StyleMe Website

A modern, responsive website for StyleMe - an AI-powered personal wardrobe stylist.

## Features

- **Landing Page**: Beautiful, modern homepage with feature highlights
- **Wardrobe Management**: Upload, organize, and manage your clothing items
- **AI Recommendations**: Get personalized outfit suggestions using AI
- **Complete the Look**: Find perfect matching items for any piece in your wardrobe
- **Stylist Chat**: Chat with an AI stylist for personalized fashion advice (requires OpenAI API key)

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (default: http://localhost:5000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (optional):
```bash
# If using Docker (default): API runs on port 5001
VITE_API_URL=http://localhost:5001

# If running API server directly (not in Docker): use port 5000
# VITE_API_URL=http://localhost:5000

# Note: OpenAI API key is now configured on the backend, not in frontend .env
# The backend handles all OpenAI API calls securely
```

3. Start the development server:
```bash
npm run dev
```

The website will be available at `http://localhost:3001`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
website/
├── src/
│   ├── components/
│   │   ├── app/          # Application screens (Home, Wardrobe, etc.)
│   │   └── ui/           # Reusable UI components
│   ├── pages/            # Page components (Landing, AppLayout)
│   ├── services/         # API service layer
│   └── lib/              # Utility functions
├── index.html
├── package.json
└── vite.config.ts
```

## Routes

- `/` - Landing page
- `/app/home` - Home screen with recent items and recommendations
- `/app/wardrobe` - Full wardrobe view with filters
- `/app/chat` - Stylist chat interface (requires OpenAI API key)
- `/app/item-details` - Individual item details

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Styling
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icons

## Development

The website is built with modern web technologies and follows best practices:

- Component-based architecture
- Type-safe with TypeScript
- Responsive design (mobile-first)
- Accessible UI components
- Optimized performance

## Notes

- The frontend code in `/frontend` remains unchanged
- All website code is in the `/website` directory
- The website uses the same API as the frontend mobile app
- **Stylist Chat Feature**: The chat feature uses GPT-4o model with vision capabilities for image analysis. The OpenAI API key is configured on the backend server (not in the frontend) for security. See backend documentation for API key setup.

