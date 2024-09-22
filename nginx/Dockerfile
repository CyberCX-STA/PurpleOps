FROM nginx:alpine

# Install OpenSSL
RUN apk add --no-cache openssl

# Set working directory
WORKDIR /etc/nginx

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