using System.Text;
using System.Text.Json;
using RabbitMQ.Client;

var builder = WebApplication.CreateBuilder(args);

// CORS
builder.Services.AddCors(options =>
    options.AddDefaultPolicy(policy => policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));

// RabbitMQ connection as singleton
builder.Services.AddSingleton<IConnection>(sp =>
{
    var factory = new ConnectionFactory
    {
        HostName = Environment.GetEnvironmentVariable("ORDER_QUEUE_HOSTNAME") ?? "rabbitmq",
        Port = int.TryParse(Environment.GetEnvironmentVariable("ORDER_QUEUE_PORT"), out var p) ? p : 5672,
        UserName = Environment.GetEnvironmentVariable("ORDER_QUEUE_USERNAME") ?? "username",
        Password = Environment.GetEnvironmentVariable("ORDER_QUEUE_PASSWORD") ?? "password"
    };
    return factory.CreateConnection();
});

var app = builder.Build();
app.UseCors();

var queueName = Environment.GetEnvironmentVariable("ORDER_QUEUE_NAME") ?? "orders";

// POST / — accept order and publish to queue
app.MapPost("/", (HttpContext ctx, IConnection connection) =>
{
    using var channel = connection.CreateModel();
    channel.QueueDeclare(queue: queueName, durable: false, exclusive: false, autoDelete: false);

    using var reader = new StreamReader(ctx.Request.Body);
    var body = reader.ReadToEndAsync().Result;

    var bodyBytes = Encoding.UTF8.GetBytes(body);
    var props = channel.CreateBasicProperties();

    channel.BasicPublish(exchange: "", routingKey: queueName, basicProperties: props, body: bodyBytes);

    Console.WriteLine($"[.NET] Order published to queue '{queueName}'");
    return Results.Created("/", JsonSerializer.Deserialize<object>(body));
});

// GET /health
app.MapGet("/health", () =>
{
    var version = Environment.GetEnvironmentVariable("APP_VERSION") ?? "1.0.0-dotnet";
    return Results.Ok(new { status = "ok", version, runtime = ".NET 8" });
});

app.Run("http://0.0.0.0:3000");
