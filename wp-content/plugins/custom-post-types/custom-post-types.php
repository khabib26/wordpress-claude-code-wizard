<?php
/**
 * Plugin Name: Custom Post Types
 * Plugin URI: https://example.com/
 * Description: Adds custom post types to WordPress
 * Version: 1.0.0
 * Author: Your Name
 * License: GPL v2 or later
 */

if (!defined('ABSPATH')) {
    exit;
}

class CustomPostTypes {
    
    public function __construct() {
        add_action('init', array($this, 'register_portfolio_post_type'));
        add_action('init', array($this, 'register_portfolio_taxonomies'));
        add_action('init', array($this, 'register_testimonial_post_type'));
    }
    
    public function register_portfolio_post_type() {
        $labels = array(
            'name'                  => _x('Portfolio', 'Post type general name', 'custom-post-types'),
            'singular_name'         => _x('Portfolio Item', 'Post type singular name', 'custom-post-types'),
            'menu_name'             => _x('Portfolio', 'Admin Menu text', 'custom-post-types'),
            'add_new'               => __('Add New', 'custom-post-types'),
            'add_new_item'          => __('Add New Portfolio Item', 'custom-post-types'),
            'edit_item'             => __('Edit Portfolio Item', 'custom-post-types'),
            'new_item'              => __('New Portfolio Item', 'custom-post-types'),
            'view_item'             => __('View Portfolio Item', 'custom-post-types'),
            'view_items'            => __('View Portfolio', 'custom-post-types'),
            'search_items'          => __('Search Portfolio', 'custom-post-types'),
            'not_found'             => __('No portfolio items found', 'custom-post-types'),
            'not_found_in_trash'    => __('No portfolio items found in Trash', 'custom-post-types'),
        );
        
        $args = array(
            'labels'             => $labels,
            'public'             => true,
            'publicly_queryable' => true,
            'show_ui'            => true,
            'show_in_menu'       => true,
            'query_var'          => true,
            'rewrite'            => array('slug' => 'portfolio'),
            'capability_type'    => 'post',
            'has_archive'        => true,
            'hierarchical'       => false,
            'menu_position'      => 5,
            'menu_icon'          => 'dashicons-portfolio',
            'supports'           => array('title', 'editor', 'thumbnail', 'excerpt', 'custom-fields'),
            'show_in_rest'       => true,
        );
        
        register_post_type('portfolio', $args);
    }
    
    public function register_portfolio_taxonomies() {
        // Portfolio Categories
        $labels = array(
            'name'              => _x('Portfolio Categories', 'taxonomy general name', 'custom-post-types'),
            'singular_name'     => _x('Portfolio Category', 'taxonomy singular name', 'custom-post-types'),
            'search_items'      => __('Search Categories', 'custom-post-types'),
            'all_items'         => __('All Categories', 'custom-post-types'),
            'edit_item'         => __('Edit Category', 'custom-post-types'),
            'update_item'       => __('Update Category', 'custom-post-types'),
            'add_new_item'      => __('Add New Category', 'custom-post-types'),
            'new_item_name'     => __('New Category Name', 'custom-post-types'),
            'menu_name'         => __('Categories', 'custom-post-types'),
        );
        
        $args = array(
            'hierarchical'      => true,
            'labels'            => $labels,
            'show_ui'           => true,
            'show_admin_column' => true,
            'query_var'         => true,
            'rewrite'           => array('slug' => 'portfolio-category'),
            'show_in_rest'      => true,
        );
        
        register_taxonomy('portfolio_category', array('portfolio'), $args);
        
        // Portfolio Tags
        $labels = array(
            'name'              => _x('Portfolio Tags', 'taxonomy general name', 'custom-post-types'),
            'singular_name'     => _x('Portfolio Tag', 'taxonomy singular name', 'custom-post-types'),
            'search_items'      => __('Search Tags', 'custom-post-types'),
            'all_items'         => __('All Tags', 'custom-post-types'),
            'edit_item'         => __('Edit Tag', 'custom-post-types'),
            'update_item'       => __('Update Tag', 'custom-post-types'),
            'add_new_item'      => __('Add New Tag', 'custom-post-types'),
            'new_item_name'     => __('New Tag Name', 'custom-post-types'),
            'menu_name'         => __('Tags', 'custom-post-types'),
        );
        
        $args = array(
            'hierarchical'      => false,
            'labels'            => $labels,
            'show_ui'           => true,
            'show_admin_column' => true,
            'query_var'         => true,
            'rewrite'           => array('slug' => 'portfolio-tag'),
            'show_in_rest'      => true,
        );
        
        register_taxonomy('portfolio_tag', array('portfolio'), $args);
    }
    
    public function register_testimonial_post_type() {
        $labels = array(
            'name'                  => _x('Testimonials', 'Post type general name', 'custom-post-types'),
            'singular_name'         => _x('Testimonial', 'Post type singular name', 'custom-post-types'),
            'menu_name'             => _x('Testimonials', 'Admin Menu text', 'custom-post-types'),
            'add_new'               => __('Add New', 'custom-post-types'),
            'add_new_item'          => __('Add New Testimonial', 'custom-post-types'),
            'edit_item'             => __('Edit Testimonial', 'custom-post-types'),
            'new_item'              => __('New Testimonial', 'custom-post-types'),
            'view_item'             => __('View Testimonial', 'custom-post-types'),
            'view_items'            => __('View Testimonials', 'custom-post-types'),
            'search_items'          => __('Search Testimonials', 'custom-post-types'),
            'not_found'             => __('No testimonials found', 'custom-post-types'),
            'not_found_in_trash'    => __('No testimonials found in Trash', 'custom-post-types'),
        );
        
        $args = array(
            'labels'             => $labels,
            'public'             => true,
            'publicly_queryable' => true,
            'show_ui'            => true,
            'show_in_menu'       => true,
            'query_var'          => true,
            'rewrite'            => array('slug' => 'testimonials'),
            'capability_type'    => 'post',
            'has_archive'        => true,
            'hierarchical'       => false,
            'menu_position'      => 6,
            'menu_icon'          => 'dashicons-format-quote',
            'supports'           => array('title', 'editor', 'thumbnail', 'custom-fields'),
            'show_in_rest'       => true,
        );
        
        register_post_type('testimonial', $args);
    }
}

// Initialize the plugin
new CustomPostTypes();

// Flush rewrite rules on activation
register_activation_hook(__FILE__, function() {
    $cpt = new CustomPostTypes();
    $cpt->register_portfolio_post_type();
    $cpt->register_portfolio_taxonomies();
    $cpt->register_testimonial_post_type();
    flush_rewrite_rules();
});

// Flush rewrite rules on deactivation
register_deactivation_hook(__FILE__, function() {
    flush_rewrite_rules();
});