FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Apache, PHP 8.3, and extensions matching DO stack
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    wget \
    && add-apt-repository ppa:ondrej/php \
    && apt-get update && apt-get install -y \
    apache2 \
    php8.3 \
    php8.3-cli \
    php8.3-common \
    php8.3-mysql \
    php8.3-xml \
    php8.3-xmlrpc \
    php8.3-curl \
    php8.3-gd \
    php8.3-imagick \
    php8.3-mbstring \
    php8.3-zip \
    php8.3-intl \
    php8.3-bz2 \
    php8.3-bcmath \
    php8.3-soap \
    libapache2-mod-php8.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Enable Apache modules
RUN a2enmod rewrite headers expires deflate ssl

# Configure PHP settings to match DO
RUN echo "upload_max_filesize = 64M" >> /etc/php/8.3/apache2/php.ini && \
    echo "post_max_size = 64M" >> /etc/php/8.3/apache2/php.ini && \
    echo "max_execution_time = 300" >> /etc/php/8.3/apache2/php.ini && \
    echo "max_input_time = 300" >> /etc/php/8.3/apache2/php.ini && \
    echo "memory_limit = 256M" >> /etc/php/8.3/apache2/php.ini

# Download and install WordPress
RUN cd /tmp && \
    wget https://wordpress.org/wordpress-6.8.1.tar.gz && \
    tar xzvf wordpress-6.8.1.tar.gz && \
    cp -R wordpress/* /var/www/html/ && \
    rm -rf /var/www/html/index.html && \
    rm -rf /tmp/wordpress*

# Set proper permissions
RUN chown -R www-data:www-data /var/www/html && \
    find /var/www/html -type d -exec chmod 755 {} \; && \
    find /var/www/html -type f -exec chmod 644 {} \;

# Apache configuration
COPY apache-config.conf /etc/apache2/sites-available/000-default.conf

EXPOSE 80

CMD ["apache2ctl", "-D", "FOREGROUND"]