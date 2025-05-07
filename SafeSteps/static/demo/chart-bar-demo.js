// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#292b2c';

// Bar Chart Example for Absence Trends
var ctx = document.getElementById("myBarChart");
var myBarChart = new Chart(ctx, {
  type: 'bar',
  data: {
    // Update labels to represent months or other time periods for absences
    labels: ["January", "February", "March", "April", "May", "June", "July"],
    datasets: [{
      label: "Absences",
      backgroundColor: "rgba(255,99,132,0.6)",  // Red color for absence bars
      borderColor: "rgba(255,99,132,1)",  // Border color for bars
      data: [5, 10, 8, 12, 6, 9, 15],  // Sample absence data
    }],
  },
  options: {
    scales: {
      xAxes: [{
        time: {
          unit: 'month'  // Set unit to 'month' to track absence trends monthly
        },
        gridLines: {
          display: false
        },
        ticks: {
          maxTicksLimit: 7  // Adjust based on how many months you are displaying
        }
      }],
      yAxes: [{
        ticks: {
          // Adjust the y-axis based on the expected number of absences
          min: 0,
          max: 20,  // Assuming the max absences for a given month is 20
          maxTicksLimit: 5
        },
        gridLines: {
          display: true
        }
      }],
    },
    legend: {
      display: false  // You can set this to true if you want a legend to appear
    }
  }
});
