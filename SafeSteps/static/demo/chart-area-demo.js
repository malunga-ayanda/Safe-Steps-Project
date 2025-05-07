// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#292b2c';

// Area Chart Example for Attendance Trends
var ctx = document.getElementById("myAreaChart");
var myLineChart = new Chart(ctx, {
  type: 'line',
  data: {
    // Update the labels to reflect specific dates for attendance tracking
    labels: ["Oct 1", "Oct 2", "Oct 3", "Oct 4", "Oct 5", "Oct 6", "Oct 7", "Oct 8", "Oct 9", "Oct 10", "Oct 11", "Oct 12", "Oct 13"],
    datasets: [{
      label: "Attendance",
      lineTension: 0.3,
      backgroundColor: "rgba(75,192,192,0.2)",  // Light teal background
      borderColor: "rgba(75,192,192,1)",  // Teal line color
      pointRadius: 5,
      pointBackgroundColor: "rgba(75,192,192,1)",  // Teal points
      pointBorderColor: "rgba(255,255,255,0.8)",
      pointHoverRadius: 5,
      pointHoverBackgroundColor: "rgba(75,192,192,1)",
      pointHitRadius: 50,
      pointBorderWidth: 2,
      // Update data to reflect the number of students present on each day
      data: [45, 50, 42, 48, 51, 47, 53, 49, 52, 50, 54, 48, 51],
    }],
  },
  options: {
    scales: {
      xAxes: [{
        time: {
          unit: 'date'
        },
        gridLines: {
          display: false
        },
        ticks: {
          maxTicksLimit: 7
        }
      }],
      yAxes: [{
        ticks: {
          // Adjust y-axis to reflect attendance numbers
          min: 0,
          max: 60,  // Assuming max attendance is 60
          maxTicksLimit: 6
        },
        gridLines: {
          color: "rgba(0, 0, 0, .125)",
        }
      }],
    },
    legend: {
      display: false
    }
  }
});
