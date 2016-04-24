angular.module('WLANThermo', ['Services', 'ngRoute']);

//create an app router for url management and redirect
angular.module('WLANThermo').config(function($routeProvider) {
    $routeProvider.when('/frontpage', {
        templateUrl: 'partials/frontpage.html',
        controller: 'FrontpageController',
    });
    $routeProvider.otherwise({redirectTo: '/frontpage'});
});

angular.module('WLANThermo').controller('FrontpageController', function($scope, Socket) {
    $scope.loading = true;
    $scope.readys = [];
    $scope.socktemp = {};
    $scope.gauges = [];


    for (i = 0; i < 8; i++) {
        $scope.gauges[i] = new JustGage({
          id: "temp"+i,
          value: i,
          min: 0,
          max: 100,
          label: "°C",
          hideInnerShadow:true,
          gaugeWidthScale:1.25,
          relativeGaugeSize:true,
          customSectors: [{
            color : "#0000FF",
            lo : 0,
            hi : 60
          },
          {
            color : "#00FF00",
            lo : 60,
            hi : 100
          }]
        });
        console.log('gauge'+i+'created');
      }

    Socket.on('hello', function(name) {
        $scope.name = name;
        $scope.loading = false;
    });

    Socket.on('ready', function() {
        $scope.readys.push('Ready Event!');

    });

    Socket.on('hello', function() {
        console.log('got an Hello');
        $scope.readys.push('Hello Event!');
    });

    Socket.on('socktemp', function(msg) {
        $scope.socktemp = csvJSON(msg);
        for (i = 0; i < 8; i++) {
          if(!$('#temp'+i).parent('.tempbox').hasClass('ng-hide')) {
            if($scope.gauges[i].config)
              $scope.gauges[i].refresh($('#temp'+i).attr('data-value'),$('#temp'+i).attr('data-min'),$('#temp'+i).attr('data-max'));
          }
        }
        $scope.graphs = [$('#temp0'),$('#temp1'),$('#temp2'),$('#temp3'),$('#temp4'),$('#temp5'),$('#temp6'),$('#temp7')];

        $.each($scope.graphs, function(index, val) {
          var graph = $(this);
          if (parseInt(graph.attr('data-value'),10) > parseInt(graph.attr('data-max'),10)) {
            graph.parent().addClass('blink hot');
          } else if (parseInt(graph.attr('data-value'),10) < parseInt(graph.attr('data-min'),10)) {
            graph.parent().addClass('blink cold');
          } else {
            graph.parent().removeClass('blink cold hot');
          }
        });
    });

    $scope.setReady = function() {
        Socket.emit('ready');
        $scope.readys.push('I AM READY!');
    };

});

angular.module('Services', []).
    factory('Socket', function($rootScope) {
        var socket = io.connect();
        return {
            on: function(eventName, callback) {
                socket.on(eventName, function() {
                    var args = arguments;
                    $rootScope.$apply(function() {
                        callback.apply(socket, args);
                    });
                });
            },
            emit: function(eventName, data, callback) {
                if(typeof data == 'function') {
                    callback = data;
                    data = {};
                }
                socket.emit(eventName, data, function() {
                    var args = arguments;
                    $rootScope.$apply(function() {
                        if(callback) {
                            callback.apply(socket, args);
                        }
                    });
                });
            },
            emitAndListen: function(eventName, data, callback) {
                this.emit(eventName, data, callback);
                this.on(eventName, callback);
            }
        };
    });


//var csv is the CSV file with headers
function csvJSON(csv){
 
  var result = {};
 
  var columns=csv.split(";");
  for (var i = 0; i < columns.length; ++i) {
    if (i == 0)
      result.time = columns[i];
    else
      result[i-1] = columns[i];
  }
  return result; 
  //JavaScript object
  //return JSON.stringify(columns); //JSON
}