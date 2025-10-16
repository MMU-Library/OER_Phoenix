#!/bin/bash
# Open Educational Resourcer - Quick Setup Script

echo "🚀 Setting up Open Educational Resourcer..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
else
    echo "✓ .env file already exists"
fi

# Make scripts executable
chmod +x docker-docker-entrypoint.sh

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Run: docker-compose up --build"
echo "3. Access the application at http://localhost:8000"
echo "4. Admin panel: http://localhost:8000/admin (admin/adminpass)"
echo ""
echo "Optional commands:"
echo "- Fetch OER resources: docker-compose exec web python manage.py fetch_oer"
echo "- Generate embeddings: docker-compose exec web python manage.py shell"
echo "  >>> from resources.services.ai_utils import generate_embeddings"
echo "  >>> generate_embeddings()"
echo ""
