#version 150

#define BLEND1

out vec4 FragColor;
in vec4 vpos;

//uniform mat4 p3d_ModelViewMatrix;
//uniform mat4 p3d_ModelViewMatrixTsranspose;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewProjectionMatrixInverse;
uniform mat4 p3d_ModelViewMatrixInverse;
uniform mat4 p3d_ModelViewMatrix;
//uniform mat4 p3d_ProjectionMatrixInverse;
//uniform mat4 p3d_ViewMatrixInverse;

uniform sampler2D depth_tex;
uniform sampler1D transfer_tex;
uniform sampler3D data_tex;
uniform sampler3D alpha_tex;

uniform vec3 light_pos;
uniform vec3 light_intensity;

uniform float focal_length;
uniform vec2 window_size;

const float max_dist = sqrt(4+4+4);

const int num_samples = 128;
const float step_size = max_dist / float(num_samples);
const float OPACITY_CORRECTION = float(128) / num_samples;

struct Ray
{
    vec4 origin;
    vec3 dir;
};


struct AABB
{
    vec4 min;
    vec4 max;
};

// http://prideout.net/blog/?p=64
bool intersect_ray_box(Ray ray, AABB aabb, out float t0, out float t1)
{
    vec3 inv_dir = 1 / ray.dir;
    vec3 t_bottom = inv_dir * (aabb.min - ray.origin).xyz;
    vec3 t_top = inv_dir * (aabb.max - ray.origin).xyz;
    vec3 t_min = min(t_top, t_bottom);
    vec3 t_max = max(t_top, t_bottom);

    vec2 t = max(t_min.xx, t_min.yz);
    t0 = max(t.x, t.y);

    t = min(t_max.xx, t_max.yz);
    t1 = min(t.x, t.y);
    return t0 <= t1;
}

void main()
{
    // Frag coord in model-space (avoid complex transforms)
    vec4 frag_model = vpos;
    //
    // vec4 v = vec4(2.0*(gl_FragCoord.x)/window_size.x-1.0,
    //           2.0*(gl_FragCoord.y)/window_size.y-1.0,
    //           2.0*texture(depth_tex,gl_FragCoord.xy).z-1.0,
    //               1.0 );
    // v = p3d_ModelViewProjectionMatrixInverse * v;
    // v /= v.w;
    // frag_model = v;

    vec4 ray_origin_model = p3d_ModelViewMatrixInverse * vec4(0, 0, 0, 1);
    vec3 to_frag_model = (frag_model - ray_origin_model).xyz;

    Ray ray = Ray(ray_origin_model, normalize(to_frag_model));
    AABB box = AABB(vec4(-1, -1, -1, 1), vec4(1, 1, 1, 1));

    float near, far;
    intersect_ray_box(ray, box, near, far);

    if (near < 0.0)
        near = 0.0;

    vec4 p_near = ray.origin + vec4(ray.dir * near, 0.0);
    vec4 p_far = ray.origin + vec4(ray.dir * far, 0.0);

    vec4 p_near_uv = (p_near + 1) / 2;
    vec4 p_far_uv = (p_far + 1) / 2;

    vec4 pos = p_near_uv;
    vec4 step = normalize(p_far_uv - p_near_uv) * step_size;
    float travel = distance(p_far_uv, p_near_uv);

    vec4 colour_acc = vec4(0.0);

    // Find screen-depth at fragment
    vec2 co = gl_FragCoord.xy / window_size;
    float depth = texture(depth_tex, co.xy).x; // This won't change

    // Do Marching
    for (int i=0; i < num_samples && travel > 0.0; i++, pos += step, travel -= step_size)
    {
        float presence = texture(alpha_tex, pos.zyx).r;
        if (presence <= 0)
            continue;

        // Ensure we don't draw on top of other model
        vec4 pos_in_clip = p3d_ModelViewProjectionMatrix * ((2 * pos)-1);
        vec3 pos_in_screen = pos_in_clip.xyz / pos_in_clip.w;
        vec3 ndc = (pos_in_screen + 1.) / 2.;

        if (depth < ndc.z)
          continue;

        float value = texture(data_tex, pos.zyx).r;
        vec4 voxel_colour = texture(transfer_tex, value);

        // DOn't consider as density - voxel_color.a *= step_size*10;
        voxel_colour.xyz *= voxel_colour.a;

        colour_acc += (1-colour_acc.a) * voxel_colour * OPACITY_CORRECTION;

        //break from the loop when has_data_array gets high enough
        if(colour_acc.a >= 0.95)
            break;
    }

    FragColor = colour_acc;// vec4(p_near.xyz, 1.);
}
