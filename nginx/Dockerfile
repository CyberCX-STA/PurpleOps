FROM nginx:alpine

# Install OpenSSL
RUN apk add --no-cache openssl

# Set working directory
WORKDIR /etc/nginx

# Create ssl directory
# RUN mkdir -p /etc/nginx/ssl

# Generate self-signed certificate
# RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#     -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt \
#     -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Copy a script to handle certificate generation or use
COPY generate_or_use_cert.sh /usr/src/app/
RUN chmod +x /usr/src/app/generate_or_use_cert.sh

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 443
EXPOSE 443

# Set the entrypoint
ENTRYPOINT ["/usr/src/app/generate_or_use_cert.sh"]

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]