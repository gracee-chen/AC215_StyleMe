# StyleMe Frontend

The StyleMe frontend is a mobile-first React application that provides an intuitive interface for users to manage their wardrobe and receive AI-powered fashion recommendations.

## Prerequisites

Before setting up the frontend, ensure you have the following installed:

- **Node.js**: Version 18.x or higher
- **npm**: Version 9.x or higher (comes with Node.js)
- **Backend API**: The StyleMe inference API server should be running (see [API Integration Guide](../docs/api_integration.md))

### Verify Installation

```bash
node --version  # Should be v18.x or higher
npm --version   # Should be 9.x or higher
```

## Environment Configuration

The frontend uses environment variables for configuration. Create a `.env` file in the `frontend/` directory to customize settings:

```bash
# .env file
VITE_API_URL=http://localhost:5000
```

### Environment Variables

- **`VITE_API_URL`** (optional): Backend API URL
  - Default: `http://localhost:5000`
  - Change this if your backend API is running on a different host or port
  - Example for production: `VITE_API_URL=https://api.styleme.example.com`

### Creating Environment File

```bash
cd frontend
echo "VITE_API_URL=http://localhost:5000" > .env
```

**Note**: Vite requires the `VITE_` prefix for environment variables to be exposed to the client-side code.

## Setup Instructions

### 1. Install Dependencies

Navigate to the frontend directory and install all required packages:

```bash
cd frontend
npm install
```

This will install all dependencies listed in `package.json`, including:
- React 18.3.1
- TypeScript
- Vite 6.3.5
- Tailwind CSS
- Radix UI components
- Other UI and utility libraries

### 2. Configure Environment (Optional)

If you need to change the default API URL, create or edit the `.env` file:

```bash
# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:5000
EOF
```

### 3. Verify Backend Connection

Ensure the backend API server is running before starting the frontend:

```bash
# From project root, start the backend API
docker-compose --profile api up inference

# Or if using the Makefile
make run-api
```

The API should be accessible at `http://localhost:5000`. You can verify by visiting `http://localhost:5000/health` in your browser.

## Running Locally

### Development Mode

Start the development server with hot module replacement:

```bash
npm run dev
```

The application will be available at:
- **Default**: `http://localhost:3000` (as configured in `vite.config.ts`)
- The terminal will display the actual URL if the port is different

### Build for Production

Create an optimized production build:

```bash
npm run build
```

The built files will be in the `frontend/build/` directory. You can serve these files with any static file server:

```bash
# Using a simple HTTP server (if installed)
npx serve -s build

# Or using Python
cd build
python -m http.server 3000
```

## Usage Guidelines

### Application Overview

StyleMe is a mobile fashion app that helps users manage their wardrobe and get AI-powered style recommendations. The frontend provides the following functionality:

### Screens and Navigation

1. **Onboarding Screen**
   - First-time user welcome screen
   - Introduces the app's features
   - Appears only on initial load

2. **Home Screen**
   - Main dashboard showing recent clothing items
   - "Add Item" button to upload new wardrobe pieces
   - Quick access to recent items

3. **Wardrobe Screen**
   - Complete view of all clothing items in the user's collection
   - Items organized by category (tops, bottoms, shoes, etc.)
   - Filter and browse functionality

4. **Item Details Screen**
   - Detailed view of a selected clothing item
   - Options to:
     - "Complete the Look" - Get style recommendations
     - Delete item from wardrobe
   - View item metadata (category, color, date added)

5. **Recommendation Screen**
   - AI-powered outfit suggestions based on selected items
   - Shows compatible items from:
     - User's personal wardrobe (if similar items exist)
     - Global catalog (Farfetch products) as fallback
   - Displays similarity scores and product details

### Key Features

- **Wardrobe Management**
  - Upload clothing items via camera or gallery
  - Organize items by category
  - View and delete items

- **Style Recommendations**
  - Get outfit suggestions based on selected items
  - AI-powered compatibility matching
  - Integration with personal wardrobe and global catalog

- **User Interface**
  - Mobile-first responsive design
  - Bottom navigation for easy access
  - Modern UI with Radix UI components
  - Tailwind CSS for styling

### API Integration

The frontend communicates with the backend API through the following endpoints:

- `POST /api/upload` - Upload wardrobe items
- `POST /api/recommend` - Get style recommendations
- `GET /api/wardrobe/<user_id>` - Retrieve user's wardrobe
- `GET /api/wardrobe/<user_id>/image/<filename>` - Serve wardrobe images

See [API Integration Guide](../docs/api_integration.md) for detailed API documentation.

## Technology Stack

- **React 18.3.1**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite 6.3.5**: Build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **React Hook Form**: Form management
- **Lucide React**: Icon library

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/              # Reusable UI components
│   │   ├── HomeScreen.tsx
│   │   ├── WardrobeScreen.tsx
│   │   ├── RecommendationScreen.tsx
│   │   └── ...
│   ├── services/            # API client and services
│   │   └── api.ts           # API integration
│   ├── styles/              # Global styles
│   │   └── globals.css
│   ├── App.tsx              # Main application component
│   └── main.tsx             # Application entry point
├── index.html               # HTML template
├── package.json             # Dependencies and scripts
├── vite.config.ts           # Vite configuration
└── README.md                # This file
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, Vite will automatically try the next available port. Check the terminal output for the actual URL.

To use a specific port, modify `vite.config.ts`:

```typescript
server: {
  port: 3001,  // Change to desired port
}
```

### Backend Connection Issues

If the frontend cannot connect to the backend:

1. Verify the backend API is running:
   ```bash
   curl http://localhost:5000/health
   ```

2. Check the `VITE_API_URL` in your `.env` file matches the backend URL

3. Ensure CORS is enabled on the backend (should be configured in `api_server.py`)

### Build Errors

If you encounter build errors:

1. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Check Node.js version compatibility:
   ```bash
   node --version  # Should be 18.x or higher
   ```

### Missing Dependencies

If you see import errors:

```bash
npm install
```

## Development Tips

- **Hot Module Replacement**: Changes to code are automatically reflected in the browser
- **TypeScript**: Use TypeScript for type safety and better IDE support
- **Component Structure**: Keep components small and focused on a single responsibility
- **API Calls**: All API calls are centralized in `src/services/api.ts`

## Next Steps

- See [Main README](../README.md) for complete project documentation
- See [API Integration Guide](../docs/api_integration.md) for backend integration details
- See [Application Design Document](../docs/Application%20design%20doc.md) for architecture overview