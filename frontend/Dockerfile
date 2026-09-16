# syntax=docker/dockerfile:1

# ---------- 開発用: flutter run(web-server) でホットリロード ----------
FROM ghcr.io/cirruslabs/flutter:stable AS dev
WORKDIR /app
ENV PUB_CACHE=/root/.pub-cache
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get
COPY . .
EXPOSE 8080
CMD ["flutter", "run", "-d", "web-server", "--web-hostname", "0.0.0.0", "--web-port", "8080"]

# ---------- 本番用: 静的ビルドして nginx で配信 ----------
FROM ghcr.io/cirruslabs/flutter:stable AS build
WORKDIR /app
ARG API_BASE_URL=http://localhost:8000
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get
COPY . .
RUN flutter build web --release --dart-define=API_BASE_URL=${API_BASE_URL}

FROM nginx:alpine AS prod
COPY --from=build /app/build/web /usr/share/nginx/html
EXPOSE 80
