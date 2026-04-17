FROM node:22-alpine AS build

WORKDIR /web
COPY package.json package-lock.json* /web/
RUN npm install

COPY . /web
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /web/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
