"use strict";

exports = module.exports = function (grunt) {

    grunt.initConfig({
        flake8: {
            options: {
                ignore: ['E501' // line too long
                ]
            },
            src: ['addons/**/*.py']
        },

        todo: {
            options: {
                file: "TODO.md", githubBoxes: true, colophon: false, usePackage: true
            },
            src: ['addons/**/*.py']
        },

        browserify: {
            preview: {
                src: "client/templates/preview/index.js",
                dest: "addons/io_scene_xml3d/templates/preview/public/scripts/xml3d-blender-preview.js"
            }
        },

        copy: {
            preview: {
                src: "addons/io_scene_xml3d/templates/preview/public/scripts/xml3d-blender-preview.js",
                dest: "output/public/scripts/xml3d-blender-preview.js"
            }
        },

        compress: {
            main: {
                options: {
                    mode: 'zip', archive: 'io_scene_xml3d-0.x.x.zip'
                },
                files: [{expand: true, cwd: 'addons/', src: ['**', '!**/__pycache__/**']}]
            }
        }
    });

    grunt.loadNpmTasks('grunt-todo');
    grunt.loadNpmTasks('grunt-browserify');
    grunt.loadNpmTasks('grunt-flake8');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-compress');

    grunt.registerTask('templates', ['browserify', 'copy']);
};
