ARG NODE_IMAGE=docker.m.daocloud.io/library/node:22-alpine
ARG NGINX_IMAGE=docker.m.daocloud.io/library/nginx:1.27-alpine

FROM ${NODE_IMAGE} AS build

ARG NPM_REGISTRY=https://registry.npmmirror.com

WORKDIR /app
COPY package*.json ./
RUN npm config set registry ${NPM_REGISTRY} \
    && npm install
COPY . .
RUN npm run build

FROM ${NGINX_IMAGE} AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
