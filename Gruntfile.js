"use strict";

exports = module.exports = function (grunt) {

    grunt.initConfig({
        flake8: {
            options: {
                ignore: ['E501' // line too long
                ]
            }, src: ['addons/**/*.py']
        },

        todo: {
            options: {
                file: "TODO.md", githubBoxes: true, colophon: false, usePackage: true
            }, src: ['addons/**/*.py']
        }
    });

    grunt.loadNpmTasks('grunt-todo');
    grunt.loadNpmTasks('grunt-flake8');
};
