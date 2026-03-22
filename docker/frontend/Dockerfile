# STAGE 1 - Development
FROM node:20-alpine AS development

WORKDIR /app

COPY package*.json ./
RUN npm install

EXPOSE 3000
CMD ["npm", "run", "dev"]


# STAGE 2 - Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build


# STAGE 3 - Production
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]