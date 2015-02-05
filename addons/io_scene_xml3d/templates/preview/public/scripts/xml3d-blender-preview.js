$(function () {

    var generator = $("meta[name=generator]").attr("content");
    var version = generator.split(" ")[1];
    console.log("Scene exported with", generator);

    var c_layers = [];
    var li = $("<li class='divider'></li><li><svg class='layers' width='125' height='45'></svg></li><li class='divider'></li>");
    $(".top-bar-section .left").append(li);
    var svg = $("svg.layers");

    function updateLayers() {
        svg.children("rect").each(function (i) {
            if (c_layers[i].active) {
                this.classList.add("active");
                //console.log("TRUE: group.layer-" + i + " > model)", document.querySelectorAll("group.layer-" + i + " > model"));
                $("group.layer-" + i + " > model").attr("visible", "true");
            } else {
                this.classList.remove("active");
                //console.log("FALSE: group.layer-" + i + " > model)", document.querySelectorAll("group.layer-" + i + " > model"));
                $("group.layer-" + i + " > model").attr("visible", "false");
            }
        });
    }

    for (var i = 0; i < 20; i++) {

        c_layers[i] = {
            active: i == 0
        };

        var rect = $(document.createElementNS("http://www.w3.org/2000/svg", "rect"));
        rect[0].classList.add("layer");

        var secondOffset = !(i < 5 || (i >= 10 && i < 15));

        rect.data("layer", i);
        rect.attr("width", "10");
        rect.attr("height", "9");
        rect.attr("x", (i % 10) * 10 + 8 + secondOffset * 10);
        rect.attr("y", (i > 9) * 9 + 13);

        rect.hover(function () {
            this.classList.add("over");
        }, function () {
            this.classList.remove("over");
        });

        rect.click(function (evt) {
            var chosen = +$(this).data("layer");
            if (evt.shiftKey) { // Toggle
                c_layers[chosen].active = !c_layers[chosen].active;
            } else {  // Activate just one
                c_layers.forEach(function (e, i) {
                    c_layers[i].active = i == chosen;
                });
            }
            updateLayers();
        });

        svg.append(rect);
    }


    //$(".top-bar-section .right").append($("")) ;
    var renderStats = $(".renderStats");

    if (window.Stats) {
        var statsLocation = $("<li class='divider'></li><li class='stats'></li>");
        $(".top-bar-section .right").append(statsLocation);
        var stats = new Stats();
        stats.setMode(0); // 0: fps, 1: ms
        //this.$el.hide();
        statsLocation.filter(".stats").append(stats.domElement);
        var loop = function () {
            stats.update();
            requestAnimationFrame(loop);
        };
        loop();
    }

    var fps = 24;
    $.get("./info/blender-config.json", function (data) {
        data.layers.forEach(function (on, i) {
            c_layers[i].active = on;
        });
        if (data.views.length) {
            var firstView = data.views[0];
            view.attr("position", firstView.translation.join(" "));
            var rot = new XML3DRotation();
            rot.setQuaternion(new XML3DVec3(firstView.rotation[1],firstView.rotation[2],firstView.rotation[3]), firstView.rotation[0])
            view.get(0).orientation.set(rot);
        }
        updateLayers();
        if(data["render-settings"]) {
            fps = data["render-settings"].fps || fps;
        }
    });

    var minFrame = 0, maxFrame = 0, currentFrame = 0;
    var animation_keys = $(".anim.armature")
    function getAnimationFrames(animations) {
        currentFrame = minFrame = Math.min.apply(Math, animations.map(function(o) { return o.minFrame }));
        maxFrame = Math.max.apply(Math, animations.map(function(o) { return o.maxFrame }));
    }


    $.get("./info/xml3d-info.json", function (data) {
        getAnimationFrames(data.animations)
        var warnings = data.warnings;
        if (warnings.length) {
            $("#bell").append("<span class='message-position'><span class='count'>" + warnings.length + "</span></span>");
            var list = $(".warningsList");
            //drop.append("<h4>Warnings</h4><hr>")
            warnings.forEach(function (warning) {
                var message = warning.message;
                if(typeof warning.issue == "number") {
                    message = message + " <a href='https://github.com/ksons/xml3d-blender-exporter/issues/"+ warning.issue + "'>Issue</a>";
                }
                list.append("<div data-alert class='alert-box secondary'><span class=''></span>" + message + "</div>");
            });
            $(document).on('opened.fndtn.reveal', '[data-reveal]', function () {
                $("#bell").children(".message-position").remove();
            });
        }
    });


    var xml3d = document.querySelector("xml3d");
    var activeObject = "";
    var renderStatText = "";

    function updateRenderText() {
        renderStats.text(version + " | " + renderStatText + (activeObject ? (" | " + activeObject) : ""));
    }

    xml3d.addEventListener("load", function () {
        $("span.fa-spin").removeClass("fa-spin fa-circle-o-notch").addClass("fa-check");
    });

    var lastAnimation = window.performance.now();
    xml3d.addEventListener("framedrawn", function (e) {
        var count = e.detail.count;
        renderStatText = "Tris:" + count.primitives + " | Objects:" + count.objects;
        updateRenderText();

        var now = window.performance.now();
        var deltaTime = now - lastAnimation;
        lastAnimation = now;

        var deltaFrame = deltaTime * fps / 1000;

         if(maxFrame > minFrame) {
            currentFrame += deltaFrame;
            if (currentFrame > maxFrame) {
                currentFrame = minFrame;
            }
            animation_keys.text(currentFrame)
        }
    });
    xml3d.addEventListener("mouseover", function (e) {
        //console.log("mouseover", e.target);
        if (e.target.nodeName == "MODEL") {
            activeObject = e.target.parentElement.id;
        } else {
            activeObject = "";
        }
        updateRenderText();
    });

    var view = $("<view id='v_pview'></view>");
    xml3d.appendChild(view.get(0));
    xml3d.setAttribute("activeView", "#v_pview");

});
