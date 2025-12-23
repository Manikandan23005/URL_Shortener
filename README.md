# URL Shortener

A simple and efficient web application that converts long URLs into short, shareable links.

## Features

- **URL Shortening**: Convert long URLs into compact, easy-to-share short links
- **Custom Aliases**: Create custom short codes for your URLs
- **QR Code Generation**: Generate QR codes for shortened URLs
- **Click Analytics**: Track the number of clicks on each shortened link
- **Expiration Dates**: Set optional expiration dates for shortened URLs
- **User-Friendly Interface**: Clean and intuitive web interface
- **RESTful API**: Programmatic access to shortening functionality

## Tech Stack

- **Backend**: Python-Flask,SQLalchemy
- **Frontend**: HTML,CSS,Jinja2
- **Database**: Sqlite
- **Additional Tools**: Docker

## Installation

### Prerequisites
- Docker
- Docker Compose

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/URL-Shortener.git
cd URL-Shortener
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build and start the application with Docker Compose:
```bash
docker-compose up -d
```

The application will be available at `http://localhost:3000`

To stop the application:
```bash
docker-compose down
```

To view logs:
```bash
docker-compose logs -f
```

## Usage

### Web Interface

1. Navigate to the home page
2. Enter your long URL in the input field
3. (Optional) Enter a custom short code
4. Click "Shorten" to generate your short URL
5. Copy the shortened link to share

### API Usage

#### Shorten a URL

```bash
POST /api/shorten
Content-Type: application/json

{
  "url": "https://example.com/very/long/url",
  "customCode": "optional-code"
}
```

#### Redirect to Original URL

```bash
GET /:shortCode
```

## Project Structure

```
URL-Shortener/
├── app/
|   ├── templates/
|   ├── static/
|   ├── __init__.py
|   ├── models.py
|   ├── route.py
├── instance/
├── migrations/
├── venv/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.