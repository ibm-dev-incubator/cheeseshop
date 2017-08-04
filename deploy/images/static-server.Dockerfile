FROM nginx:1.13-alpine

COPY ./cheeseshop/static /cheeseshop-static
COPY ./conf/static-nginx.conf /etc/nginx/conf.d/cheeseshop-static.template

CMD ["/bin/bash", "-c", "envsubst < /etc/nginx/conf.d/cheeseshop-static.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
