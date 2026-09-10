# 构建阶段
FROM node:20-alpine AS build
WORKDIR /app

# npm 镜像（国内网络可用 npmmirror；海外可 --build-arg NPM_REGISTRY=https://registry.npmjs.org）
ARG NPM_REGISTRY=https://registry.npmmirror.com

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=${NPM_REGISTRY}
COPY frontend/ ./
RUN npm run build

# 运行阶段：nginx 托管静态资源 + 反向代理 /api
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
